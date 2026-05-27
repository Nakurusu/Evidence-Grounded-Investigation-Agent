from fastapi import APIRouter, UploadFile, BackgroundTasks
from services.pipeline import process_uploaded_file
from services.task_store import TASK_RESULTS
import uuid
from datetime import datetime, UTC

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

@router.post("/")
async def upload(
    background_tasks: BackgroundTasks, 
    file: UploadFile
):

    task_id = str(uuid.uuid4())

    TASK_RESULTS[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "filename": file.filename,
        "created_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "result": None,
        "error": None
    }

    background_tasks.add_task(
        process_uploaded_file, 
        task_id,
        file
        )

    return {
        "task_id": task_id,
        "status": "processing"
    }