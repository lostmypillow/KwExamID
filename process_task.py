import asyncio
from playwright.async_api import async_playwright, Page
from concurrent.futures import ThreadPoolExecutor
from database.async_operations import update_failure, update_success
from solve_captcha_sync import solve_captcha_sync
from tqdm.asyncio import tqdm_asyncio
from results import failed_tasks, failed_list, succeeded_tasks
async def fill_details(page: Page, student: dict):
    """Reusable function to fill details into page (also after captcha failure)

    Parameters
    ----------
    page : Page
        Page instance passed in from process_task()
    student : dict
        the student dictionary from asyncio.Queue
    """
    await page.fill("input#PID", student['personal_id'])
    await page.locator("#PBdYear").select_option(student['year'])
    await page.locator("#PBdMon").select_option(student['month'])
    await page.locator("#PBdDay").select_option(student['day'])


async def process_task(student: dict, progress_bar: tqdm_asyncio):
    """_summary_

    Parameters
    ----------
    queue : asyncio.Queue
        _description_
    semaphore : asyncio.Semaphore
        _description_
    executor : ThreadPoolExecutor
        _description_
    """
    global succeeded_tasks, failed_list, failed_tasks, total_tasks
    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)
        progress_bar.update(1)

        context = await browser.new_context(
            viewport={"width": 640, "height": 360})
        progress_bar.update(1)
        
        page = await context.new_page()
        progress_bar.update(1)

        captcha_attempts = 0

        login_success = False

        try:
            # Navigate and interact with the page
            await page.goto("https://ap.ceec.edu.tw/RegExam/RegInfo/Login?examtype=A")
            progress_bar.update(1)

            await page.wait_for_load_state("networkidle")
            progress_bar.update(1)

            await fill_details(page, student)
            progress_bar.update(1)

            while login_success == False:
                if captcha_attempts < 3:

                    captcha_attempts += 1
                else:
                    # await update_failure(student.student_id)
                    print(f"Extraction failure: {student['name']}")
                    
                    failed_list.append(student)
                    break
                # print(
                #     f"Captcha Solve Attempt No. {captcha_attempts} starting...")
                img_bytes = await page.locator('img#valiCode').screenshot()
                solved_captcha = await asyncio.to_thread(solve_captcha_sync, img_bytes
                                                         )
                

                # If captcha solver outputs None = it cannot recognize any number of digits and cannot produce a number
                if solved_captcha is None:

                    # This selects the button/captcha image and clicks it, effectively refreshing the image
                    await page.locator("button.btn.btn-default").first.click()

                    # We skip the rest and start the loop again
                    continue
                progress_bar.update(1)

                await page.fill("input#Captcha", str(solved_captcha))
                progress_bar.update(1)

                await page.locator("button#login").click()
                progress_bar.update(1)

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
            progress_bar.update(1)
            # If login sucess and the div containing teh exam ID is present...
            if login_success and await page.locator(
                    'div.col-6.col-md-9.p-3.border').nth(1).count() > 0:

                exam_id = await page.locator(
                    'div.col-6.col-md-9.p-3.border').nth(1).inner_text()
                # Update database of success and extracted exam ID
                await update_success(student['student_id'], exam_id)
                succeeded_tasks += 1
                progress_bar.update(1)
                # print(f"Extraction success: {student ['student_id']} {student['name']}, exam ID: {exam_id}")

                

            # If any of the conditions is not true...
            else:
                # Inform database of failure to extract info
                await update_failure(student['student_id'])
                
                failed_list.append(student)
                progress_bar.update(1)
                # print(f"Extraction failure: {student ['student_id']} {student['name']}")
            

        finally:
            
            await browser.close()
            
