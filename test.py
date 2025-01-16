# from lib.extractor import Extractor
from database.async_operations import fetch_all_sql
import asyncio
# load_dotenv()

# from captcha_solver import CaptchaSolver
# c = CaptchaSolver()
# print("im clean")
# print(os.environ)
# import os
# import asyncio
async def test():
    result = await fetch_all_sql("get_all_students")
    print(result)
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