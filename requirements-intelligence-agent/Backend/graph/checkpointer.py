import os

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()


CONNECTION_STRING = os.getenv("CONNECTION_STRING")

if not CONNECTION_STRING:
    raise RuntimeError(
        "CONNECTION_STRING environment variable is not set."
    )


pool = ConnectionPool(
    conninfo=CONNECTION_STRING,
    max_size=10,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
)


checkpointer = PostgresSaver(pool)