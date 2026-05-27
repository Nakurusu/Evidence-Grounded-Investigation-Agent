from pathlib import Path
import shutil

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(exist_ok=True)

def save_uploaded_file(file, task_id):

    file_path = (
        UPLOAD_DIR /
        f"{task_id}_{file.filename}"
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(file.file, buffer)

    return str(file_path)