# from lib.extractor import Extractor


load_dotenv()

from captcha_solver import CaptchaSolver
c = CaptchaSolver()
print("im clean")
# print(os.environ)
# import os
# import asyncio
# async def test():
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

# asyncio.run(test())