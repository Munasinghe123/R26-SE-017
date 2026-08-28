import os
import uuid

import db.config as db

from utils.saveFile import save_file
from graph.instance import graph
from services.meetings_service import save_srs_draft


async def handle_document_upload(file, project_id):

    print("DOCUMENT PROJECT ID:", project_id)

    path = save_file(file)

    thread_id = str(uuid.uuid4())

    try:

        # ---------------------------------------------------------
        # Store the LangGraph thread ID against the project
        # ---------------------------------------------------------

        async with db.pool.acquire() as connection:

           await connection.execute(
    """
    UPDATE projects
    SET
        thread_id = $1,
        analysis_status = 'waiting'
    WHERE id = $2
    """,
    thread_id,
    project_id
)

        print("PROJECT THREAD ID:", thread_id)

        # ---------------------------------------------------------
        # Start LangGraph workflow
        # ---------------------------------------------------------

        result = graph.invoke(
            {
                "mode": "document_extract",
                "document_path": path,
                "project_id": project_id,
                "thread_id": thread_id,
                "iteration_count": 0,
                "feedback_history": [],
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        # ---------------------------------------------------------
        # Optional SRS draft
        # ---------------------------------------------------------

        # await save_srs_draft(
        #     project_id,
        #     result["requirements"]
        # )

        print("THREAD ID:", thread_id)

        return {
            "thread_id": thread_id
        }

    finally:

        if os.path.exists(path):

            os.remove(path)

            print(
                f"Temporary document deleted: {path}"
            )