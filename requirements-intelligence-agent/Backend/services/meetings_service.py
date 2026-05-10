
import json
import uuid
from db.config import get_connection

def save_requirements(requirements):
    conn = get_connection()
    cursor = conn.cursor()

    meeting_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO meetings (id) VALUES (%s)",
        (meeting_id,)
    )

    cursor.execute(
        """
        INSERT INTO requirements 
        (meeting_id, version, functional, non_functional)
        VALUES (%s, %s, %s, %s)
        """,
        (
            meeting_id,
            1,
            json.dumps(requirements["functional"]),
            json.dumps(requirements["non_functional"])
        )
    )

    conn.commit()
    conn.close()

    return meeting_id

def get_latest_requirements(meeting_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT functional, non_functional, version
        FROM requirements
        WHERE meeting_id = %s
        ORDER BY version DESC
        LIMIT 1
        """,
        (meeting_id,)
    )

    result = cursor.fetchone()
    conn.close()
    
    if result:
        import json
        result["functional"] = json.loads(result["functional"])
        result["non_functional"] = json.loads(result["non_functional"])

    return result

def save_refined_version(meeting_id, requirements, feedback):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT MAX(version) as latest_version
        FROM requirements
        WHERE meeting_id = %s
        """,
        (meeting_id,)
    )

    result = cursor.fetchone()

    latest_version = result["latest_version"] or 0

    new_version = latest_version + 1

    cursor.execute(
        """
        INSERT INTO requirements
        (meeting_id, version, functional, non_functional, feedback)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            meeting_id,
            new_version,
            json.dumps(requirements["functional"]),
            json.dumps(requirements["non_functional"]),
            feedback
        )
    )

    conn.commit()
    conn.close()

    return new_version
    

