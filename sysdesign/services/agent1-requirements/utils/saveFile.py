import os
import uuid
import shutil

def save_file(file):
    os.makedirs("temp", exist_ok=True)

    # extract extension safely
    ext = os.path.splitext(file.filename)[1]  # .mp3, .mp4, etc.

    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join("temp", filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return path