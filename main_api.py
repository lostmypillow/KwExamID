from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from concurrent.futures import ProcessPoolExecutor
import asyncio
from process_task import process_task
from database.async_operations import exec_sql, async_engine
import logging


async def lifespan(app: FastAPI):
    yield
    if async_engine:
        print("Disposing async SQLAlchemy engine...", end="")
        await async_engine.dispose()
        print("Done!")


app = FastAPI(lifespan=lifespan)

# Executor to handle CPU-bound tasks
executor = ProcessPoolExecutor(max_workers=4)


async def process_and_send(student: dict, websocket: WebSocket):
    """Process a student task and send progress updates via WebSocket."""
    try:
        async for update in process_task(student):
            await websocket.send_json({
                "student": update['student_id'],
                "progress": update["progress"]
            })
        await websocket.send_json({
            "student": update['student_id'],
            "progress": "Complete"
        })
    except Exception as e:
        print(f"Error processing {update['student_id']}: {str(e)}")
        await websocket.send_json({
            "student": update['student_id'],
            "progress": "Failed"
        })


@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    students = await exec_sql("all", "get_all_students")
    students = [dict(student) for student in students]
    await websocket.send_json({"all_students": students})

    for student in students:
        # Instead of tqdm, send updates via WebSocket
        await process_and_send(student, websocket)

    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    uvicorn.run(app, host="0.0.0.0", port=8000)
    webbrowser.open('http://localhost:8000')

