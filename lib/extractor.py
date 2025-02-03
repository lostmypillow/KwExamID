from playwright.async_api import async_playwright, Playwright
import os
import time
from ..captcha_solver import CaptchaSolver
from database.async_operations import update_failure, update_success
from datetime import date


class Extractor:
    def __init__(self, student):
        self.status = ""
        self.captcha_attempt_count = 0
        self.personal_id = str(student["personal_id"])
        self.student_id = student["student_id"]
        self.year = str(student["year"] - 1911)
        self.month = str(student["month"]).zfill(2)
        self.day = str(student["day"]).zfill(2)
        self.exam_id = ""

    async def solve_captcha(self, page):
        """Handle captcha solving logic."""
        await page.locator('img#valiCode').screenshot(
            path=os.path.dirname(__file__) + "/images/" + "screenshot.png")
        start_time = time.perf_counter()
        solver = CaptchaSolver(os.path.dirname(
            __file__) + "/images/" + "screenshot.png")
        result = solver.solve_captcha()
        real_result = result[1] if type(result) == list else result
        end_time = time.perf_counter()
        if real_result:
            print(f"result: {real_result}")
            await page.fill("input#Captcha", str(real_result))
            print(
                f"Captcha filled in successfully in {end_time - start_time} seconds!")
            return True
        else:
            print("Captcha solving failed, retrying...")
            return False

    async def attempt_login(self, page):
        """Attempt to solve the captcha, click the login button, and check the response."""
        while True:
            if self.captcha_attempt_count < 3:
                self.captcha_attempt_count += 1
            else:
                return False
            print(
                f"Captcha Solve Attempt No. {self.captcha_attempt_count} starting...")
            if await self.solve_captcha(page):
                await page.locator("button#login").click()
                error_element = page.locator("div.jconfirm-content")
                if await error_element.count() == 0:
                    return True
                if await error_element.inner_text() == "-驗證碼輸入錯誤":
                    print("Captcha wrong, retrying")
                    await page.locator(
                        'button.btn.btn-default:has-text("ok")').click()
                    await self.fill_details(page)
                    continue
                else:
                    await update_failure(self.student_id)
                    return False
            else:
                await page.locator("button.btn.btn-default").first.click()

    async def fill_details(self, page):
        await page.fill("input#PID", self.personal_id)
        await page.locator("#PBdYear").select_option(self.year)
        await page.locator("#PBdMon").select_option(self.month)
        await page.locator("#PBdDay").select_option(self.day)

    async def extract_info(self, page):
        print("Extraction Success")
        if await page.locator(
                'div.col-6.col-md-9.p-3.border').nth(1).count() > 0:
            await update_success(self.student_id, await page.locator(
                'div.col-6.col-md-9.p-3.border').nth(1).inner_text())
        else:
            await update_failure(self.student_id)

    async def start(self):
        """Main logic for browser interaction."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
            viewport={"width": 640, "height": 360})
            page = await context.new_page()
            await page.goto("https://ap.ceec.edu.tw/RegExam/RegInfo/Login?examtype=A")
            await page.wait_for_load_state("networkidle")
            await self.fill_details(page)
            login_attempt = await self.attempt_login(page)
            if login_attempt is True:
                await self.extract_info(page)
