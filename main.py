import asyncio
import logging
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from database.async_operations import fetch_all_sql, async_engine
from dotenv import load_dotenv
from .process_task import process_task

async def main():

    # Creates an asyncio Queue (different from normal Python built-in queue)
    student_queue = asyncio.Queue()

    # Fetches all the student data. Once.
    #
    # This makes my whole application different from KwExamID_winforms which fetches the list once *for every student on the list*. Which I deem unnecessary and inefficient.
    all_students = await fetch_all_sql("get_all_students")

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
    await async_engine.dispose()


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

