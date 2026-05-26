from fastapi import APIRouter, UploadFile
from services.pipeline import process_uploaded_file
import uuid
from services.task_store import TASK_RESULTS

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

@router.post("/")
async def upload(file: UploadFile):

    task_id = str(uuid.uuid4())

    result = process_uploaded_file(file)

    TASK_RESULTS[task_id] = result

    return {
        "task_id": task_id
    }