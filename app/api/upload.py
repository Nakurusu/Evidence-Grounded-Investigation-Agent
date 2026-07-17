from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends
from app.services.pipeline import (
    process_uploaded_file,
    process_multi_dataset_upload,
)
from app.services.file_manager import save_uploaded_file
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.task import Task
import uuid
from datetime import datetime, UTC
from app.core.logger import logger
from app.models.enums import TaskStatus

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
    logger.info(
        f"received upload: {file.filename}"
    )

    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        status=TaskStatus.PENDING.value,
        filename=file.filename,
        created_at=datetime.now(UTC)
    )
    db.add(task)
    db.commit()
    logger.info(
        f"created task: {task_id}"
)

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
        "status": TaskStatus.PENDING.value
    }


@router.post("/investigate/")
async def investigate(
    background_tasks: BackgroundTasks,
    primary_file: UploadFile,
    secondary_files: list[UploadFile] | None = None,
    db: Session = Depends(get_db),
):
    """Investigate a primary dataset with optional secondary datasets.

    Runs the full pipeline on the primary file and cross-dataset analysis
    if secondary files are provided (Phase 9).
    """
    logger.info(
        f"received investigation: primary={primary_file.filename}"
        + (
            f", secondary={[f.filename for f in secondary_files]}"
            if secondary_files else ""
        )
    )

    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        status=TaskStatus.PENDING.value,
        filename=primary_file.filename,
        created_at=datetime.now(UTC),
    )
    db.add(task)
    db.commit()
    logger.info(f"created task: {task_id}")

    primary_path = save_uploaded_file(primary_file, task_id)
    secondary_paths = []
    if secondary_files:
        for sf in secondary_files:
            secondary_paths.append(save_uploaded_file(sf, task_id))

    background_tasks.add_task(
        process_multi_dataset_upload,
        task_id,
        primary_path,
        secondary_paths,
    )

    return {
        "task_id": task_id,
        "status": TaskStatus.PENDING.value,
        "primary": primary_file.filename,
        "secondary": [f.filename for f in secondary_files] if secondary_files else [],
    }