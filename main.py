print("Initializing KwExamID...")
import asyncio
import logging
import sys
import subprocess
from database.async_operations import exec_sql, async_engine
from dotenv import load_dotenv
from process_task import process_task
from tqdm.asyncio import tqdm
from results import succeeded_tasks, failed_list, failed_tasks, total_tasks
from pprint import pprint

async def main():
    global succeeded_tasks, failed_list, failed_tasks, total_tasks

    # Creates an asyncio Queue (different from normal Python built-in queue)
    student_queue = asyncio.Queue()

    # Fetches all the student data. Once.
    #
    # This makes my whole application different from KwExamID_winforms which fetches the list once *for every student on the list*. Which I deem unnecessary and inefficient.
    print("Adding students from database to queue...", end="")
    # TODO Test with real student data
    all_students = await exec_sql("all", "get_all_students")
    # We process the every result tuple in list
    for student_tuple in all_students:

        # keys for the future constructed dictionary
        data_keys = ('personal_id',
                     'student_id',
                     'name',
                     'year',
                     'month',
                     'day')

        # If the number of keys match the number of values in the tuples, we move on to creation of dict
        if len(data_keys) == len(student_tuple):

            # this constructs the dictionary student_tuple and the data_keys tuple...with the data keys as keys, student tuple as values
            student_dict = {
                data_keys[i]: student_tuple[i]
                for i, _ in enumerate(student_tuple)
            }

            # we go back and convert all the years to 民國 years
            student_dict["year"] = str(student_dict["year"] - 1911)

            # Convert the months from like 9 to 09
            student_dict["month"] = str(student_dict["month"]).zfill(2)

            # Convert the days from like 9 to 09
            student_dict["day"] = str(student_dict["day"]).zfill(2)

            # Put the student in the asyncio Queue
            await student_queue.put(student_dict)

    print("Done!")
    total_tasks = student_queue.qsize()
    print("Starting queue...")
    # Process each student one after the other
    while not student_queue.empty():
        student = await student_queue.get()
        with tqdm(total=11, desc=f"{student['student_id']} {student['name']}") as progress_bar:
            await process_task(student, progress_bar)

        student_queue.task_done()  # Mark the task as done
    await student_queue.join()
    print("Done!")
    if async_engine:
        print("Disposing async SQLAlchemy engine...", end="")
        await async_engine.dispose()
        print("Done!")
    print("[REPORT]")
    print(f"Succeeded: {succeeded_tasks}/{total_tasks}")
    print(f"Failed: {len(failed_list)}/{total_tasks}")
    print(f"Failed tasks:")
    pprint(failed_list)


# Load .env values
load_dotenv()

# Disable logging for the goddamn annoying transformer and tensorflow  console output
logging.disable(logging.WARNING)

print("Ensuring browsers for playwright are installed...", end="")
# for some reason it doesn't automatically do that when we pip install for the first time
subprocess.run(
    [sys.executable, "-m", "playwright", "install"],
    check=True,
)
print("Done!")


# Run the main function
asyncio.run(main())
