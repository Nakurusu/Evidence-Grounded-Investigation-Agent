from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends
from services.pipeline import process_uploaded_file
from services.file_manager import save_uploaded_file
from sqlalchemy.orm import Session
from db.dependencies import get_db
from models.task import Task
import uuid
from datetime import datetime, UTC

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

@router.post("/")
async def upload(
    background_tasks: BackgroundTasks, 
    file: UploadFile,
    db: Session = Depends(get_db)
):

    task_id = str(uuid.uuid4())

    
    task = Task(
        id=task_id,
        status="processing",
        filename=file.filename,
        created_at=datetime.now(UTC)
    )

    db.add(task)
    db.commit()

    file_path = save_uploaded_file(
        file, 
        task_id
        )

    background_tasks.add_task(
        process_uploaded_file, 
        task_id,
        file_path
        )

    return {
        "task_id": task_id,
        "status": "processing"
    }