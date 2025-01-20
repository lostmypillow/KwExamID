# from lib.extractor import Extractor
from database.async_operations import exec_sql, async_engine
import asyncio
# load_dotenv()

# from captcha_solver import CaptchaSolver
# c = CaptchaSolver()
# print("im clean")
# print(os.environ)
# import os
# import asyncio
async def test():
    all_students = await exec_sql("all", "get_all_students")
    print(all_students)
    await async_engine.dispose()
#     mock_person = {
#       "personal_id": "F132481419",
#       "student_id": "090705",
#       "name": "洪翊鈞",
#       "year": 2007,
#       "month": 9,
#       "day": 20,
#       "status": "pending"
#     }
#     extractor = Extractor(mock_person)
#     await extractor.start()

asyncio.run(test())