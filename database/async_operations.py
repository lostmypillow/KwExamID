from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from typing import Any
import pathlib
import os
from datetime import date
connection_url = "mssql+aioodbc://testsql:test123456@192.168.2.8/JLL2?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
async_engine = create_async_engine(
    connection_url, pool_size=100, max_overflow=0, pool_pre_ping=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def sql_from_file(command_name):
    file_path = os.path.join(pathlib.Path(
        __file__).parent.resolve(), 'sql', command_name + '.sql')
    with open(file_path, 'r', encoding="utf-8") as file_buffer:
        return file_buffer.read()


async def commit_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        await session.execute(text(sql_command), kwargs)
        await session.commit()


async def fetch_one_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        result = await session.execute(text(sql_command), kwargs)
        return result.fetchone()


async def fetch_all_sql(command_name, **kwargs):
    async with async_session() as session:
        sql_command = await sql_from_file(command_name)
        result = await session.execute(text(sql_command), kwargs)
        all_results = result.fetchall()
        return all_results
        # return [dict(row) for row in all_results]


async def update_failure(student_id):
    await commit_sql(
        "update_exam_id",
        student_id=student_id,
        exam_id="查無考生 (資料錯誤)",
        status_msg=date.today().strftime("%Y%m%d") + "資料錯誤")


async def update_success(student_id, exam_id):
    await commit_sql(
        "update_exam_id",
        student_id=student_id,
        exam_id=exam_id,
        status_msg=date.today().strftime("%Y%m%d"))
