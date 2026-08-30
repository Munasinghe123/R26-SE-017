import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("CONNECTION_STRING")

pool = None


async def connect_db():
    global pool

    pool = await asyncpg.create_pool(
        CONNECTION_STRING
    )


async def close_db():
    global pool

    if pool:
        await pool.close()