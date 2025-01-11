import asyncio
import os
import logging
import sys
import subprocess
from playwright.async_api import async_playwright, Page
from concurrent.futures import ThreadPoolExecutor
from database.async_operations import fetch_all_sql, update_failure, update_success
from dotenv import load_dotenv
from captcha_solver import CaptchaSolver

screenshot_path = os.path.dirname(__file__) + "/images/" + "screenshot.png"


def solve_captcha_sync(image:bytes):
    # Simulate the blocking CPU-intensive captcha-solving function
    solver = CaptchaSolver(image)
    result = solver.solve_captcha()
    print(f"captcha result: {result}")
    return result


async def fill_details(page: Page, student: dict):
    await page.fill("input#PID", student['personal_id'])
    await page.locator("#PBdYear").select_option(student['year'])
    await page.locator("#PBdMon").select_option(student['month'])
    await page.locator("#PBdDay").select_option(student['day'])


async def process_task(
        queue: asyncio.Queue,
        semaphore: asyncio.Semaphore,
        executor: ThreadPoolExecutor):
    async with semaphore:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 640, "height": 360})
            page = await context.new_page()
            captcha_attempts = 0
            login_success = False
            try:
                student = await queue.get()

                # Navigate and interact with the page
                await page.goto("https://ap.ceec.edu.tw/RegExam/RegInfo/Login?examtype=A")

                await page.wait_for_load_state("networkidle")

                await fill_details(page, student)

                while login_success == False:

                    if captcha_attempts < 3:
                        captcha_attempts += 1
                    else:
                        # await update_failure(student.student_id)
                        break
                    print(
                        f"Captcha Solve Attempt No. {captcha_attempts} starting...")
                    img_bytes = await page.locator('img#valiCode').screenshot()
                    solved_captcha = await asyncio.get_event_loop().run_in_executor(
                        executor, solve_captcha_sync, img_bytes
                    )

                    # If captcha solver outputs None = it cannot recognize any number of digits and cannot produce a number
                    if solved_captcha is None:

                        # This selects the button/captcha image and clicks it, effectively refreshing the image
                        await page.locator("button.btn.btn-default").first.click()

                        # We skip the rest and start the loop again
                        continue

                    await page.fill("input#Captcha", str(solved_captcha))

                    await page.locator("button#login").click()

                    error_element = page.locator("div.jconfirm-content")

                    # If there are no error elements present = input details successful
                    if await error_element.count() == 0:

                        # Update login success state
                        login_success = True

                        # Break out of while loop
                        break

                    # If error element has inner text of wrong captcha...
                    if await error_element.inner_text() == "-驗證碼輸入錯誤":

                        # Click the ok button to dismiss the dialog
                        await page.locator(
                            'button.btn.btn-default:has-text("ok")').click()

                        # Fill the same details again
                        await fill_details(page, student)

                        # Loop back to "while True"
                        continue

                    # If the dialog displays any other error message...
                    else:

                       # Update login success status as False
                        login_success = False

                        # Break out of the while loop
                        break

                # If login sucess and the div containing teh exam ID is present...
                if login_success and await page.locator(
                        'div.col-6.col-md-9.p-3.border').nth(1).count() > 0:

                    exam_id = await page.locator(
                        'div.col-6.col-md-9.p-3.border').nth(1).inner_text()
                    # Update database of success and extracted exam ID
                    # await update_success(student.student_id, exam_id)

                    print(
                        f"Extraction success: {student['name']}, exam ID: {exam_id}")

                # If any of the conditions is not true...
                else:
                    # Inform database of failure to extract info
                    # await update_failure(student.student_id)

                    print(f"Extraction failure: {student['name']}")

            finally:
                await browser.close()
                queue.task_done()


async def main():
    student_queue = asyncio.Queue()
    
    all_students = await fetch_all_sql("get_all_students")
    for student_tuple in all_students:
        data_keys = ('personal_id',
                     'student_id',
                     'name',
                     'year',
                     'month',
                     'day')
        if len(data_keys) == len(student_tuple):
            student_dict = {data_keys[i]: student_tuple[i]  for i, _ in enumerate(student_tuple)}
            student_dict["year"] = str(student_dict["year"] - 1911)
            student_dict["month"] = str(student_dict["month"]).zfill(2)
            student_dict["day"] = str(student_dict["day"]).zfill(2)
            await student_queue.put(student_dict)
    

    # Semaphore to limit concurrent browsers
    semaphore = asyncio.Semaphore(4)

    # Create a ThreadPoolExecutor for captcha-solving
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Create and run tasks
        tasks = [asyncio.create_task(process_task(
            student_queue, semaphore, executor)) for _ in range(4)]

        # Wait for the queue to be fully processed
        await student_queue.join()

        # Cancel any leftover tasks
        for task in tasks:
            task.cancel()


# Load .env values
load_dotenv()

# Disable logging for the goddamn annoying transformer and tensorflow  console output
logging.disable(logging.WARNING)

# Ensures browsers for playwright are installed (for some reason it doesn't automatically do thaat when we pip install)
subprocess.run(
    [sys.executable, "-m", "playwright", "install"],
    check=True,
)


# Run the main function
asyncio.run(main())
