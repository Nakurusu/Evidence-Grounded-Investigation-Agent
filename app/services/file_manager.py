from pathlib import Path
import shutil
from app.core.settings import settings

UPLOAD_DIR = Path(settings.UPLOAD_DIR)

UPLOAD_DIR.mkdir(exist_ok=True)

def save_uploaded_file(file, task_id):

    file_path = (
        UPLOAD_DIR /
        f"{task_id}_{file.filename}"
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(file.file, buffer)

    return str(file_path)


def get_uploaded_file_path(task_id, filename):
    """Return the persisted upload path for a task.

    Uploaded files are saved with the task id prefix so follow-up analyses can
    re-run deterministic calculations from the original dataset.
    """

    expected_path = UPLOAD_DIR / f"{task_id}_{filename}"
    if expected_path.exists():
        return str(expected_path)

    matches = list(UPLOAD_DIR.glob(f"{task_id}_*"))
    if matches:
        return str(matches[0])

    raise FileNotFoundError(
        f"Uploaded file for task {task_id} was not found"
    )
