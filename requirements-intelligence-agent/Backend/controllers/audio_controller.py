import os
import uuid

import db.config as db

from utils.saveFile import save_file
from graph.instance import graph


async def handle_audio_upload(file, project_id):

    print("AUDIO PROJECT ID:", project_id)

    path = save_file(file)

    thread_id = str(uuid.uuid4())

    try:

        # Store the active LangGraph thread
        # against this project.
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

        result = graph.invoke(
            {
                "mode": "audio_extract",
                "audio_path": path,
                "project_id": project_id,
                "thread_id": thread_id,
                "iteration_count": 0,
                "feedback_history": [],
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        print("MEETING ID:", thread_id)

        return {
            "thread_id": thread_id
        }

    finally:

        if os.path.exists(path):

            os.remove(path)

            print(
                f"Temporary audio deleted: {path}"
            )