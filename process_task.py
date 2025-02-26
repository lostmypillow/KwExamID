import asyncio
from playwright.async_api import async_playwright, Page
from database.async_operations import update_failure, update_success
from captcha_solver import captcha_solver

async def fill_details(page: Page, student: dict):
    """Reusable function to fill details into the page (also after captcha failure)."""
    await page.fill("input#PID", student['身分證'])
    await page.locator("#PBdYear").select_option(str(student["生日"].year - 1911))
    await page.locator("#PBdMon").select_option(str(student["生日"].month).zfill(2))
    await page.locator("#PBdDay").select_option(str(student["生日"].day).zfill(2))

async def process_task(student: dict):
    """Process student task and yield progress updates instead of using tqdm."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 640, "height": 360})
        page = await context.new_page()

        captcha_attempts = 0
        login_success = False

        try:
            await page.goto("https://ap.ceec.edu.tw/RegExam/RegInfo/Login?examtype=A")
            await page.wait_for_load_state("networkidle")
            await fill_details(page, student)

            while login_success == False:
                if captcha_attempts < 3:
                    captcha_attempts += 1
                else:
                    failed_list.append(student)
                    yield {
                        "student_id": student['學號'],
                        "progress": 100,
                        "message": "Failed due to captcha"
                        }
                    break

                img_bytes = await page.locator('img#valiCode').screenshot()
                solved_captcha = await asyncio.to_thread(captcha_solver, img_bytes)

                if solved_captcha is None:
                    await page.locator("button.btn.btn-default").first.click()
                    continue

                await page.fill("input#Captcha", str(solved_captcha))
                await page.locator("button#login").click()
                error_element = page.locator("div.jconfirm-content")

                if await error_element.count() == 0:
                    login_success = True
                    break

                if await error_element.inner_text() == "-驗證碼輸入錯誤":
                    await page.locator('button.btn.btn-default:has-text("ok")').click()
                    await fill_details(page, student)
                    continue

                login_success = False
                break

            if login_success and await page.locator('div.col-6.col-md-9.p-3.border').nth(1).count() > 0:
                exam_id = await page.locator('div.col-6.col-md-9.p-3.border').nth(1).inner_text()
                await update_success(student['學號'], exam_id)
                yield {
                    "student_id": student['學號'],
                    "progress": 100,
                    "message": "Success"
                    }

            else:
                await update_failure(student['學號'])
                failed_list.append(student)
                yield {
                    "student_id": student['學號'],
                    "progress": "Failed to extract exam ID"
                    }

        finally:
            await browser.close()
