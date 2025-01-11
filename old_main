from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from asyncio import sleep
from dotenv import load_dotenv
from database.async_operations import fetch_all_sql
from datetime import date, datetime
from queue import Queue
from lib.extractor import Extractor
q = Queue()
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/start")
async def start_auto_extract():
    if q.empty():
        all_students = await fetch_all_sql("get_all_students")
        for student in all_students:
            q.put({
                'personal_id': student[0],
                'student_id': student[1],
                'name': student[2],
                'year': student[3].year,
                'month': student[3].month,
                'day': student[3].day
            })
    while not q.empty():
        extractor = Extractor(q.get())
        print(f"Running {extractor.student_id}")
        if int(extractor.year)> 90:
            await extractor.start()
    return "okkkkkk"
