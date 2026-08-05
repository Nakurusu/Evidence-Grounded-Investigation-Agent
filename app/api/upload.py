from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends, File, Form
from app.services.pipeline import (
    process_uploaded_file,
    process_multi_dataset_upload,
)
from app.services.file_manager import save_uploaded_file
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.task import Task
import uuid
from datetime import datetime, timezone
from app.core.logger import logger
from app.models.enums import TaskStatus

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)


def _normalize_investigation_question(question: str | None) -> str | None:
    if question is None:
        return None
    cleaned = question.strip()
    return cleaned or None

@router.post("/")
async def upload(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    investigation_question: str | None = Form(None),
    db: Session = Depends(get_db)
):
    normalized_question = _normalize_investigation_question(
        investigation_question
    )
    logger.info(
        f"received upload: {file.filename}"
    )

    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        status=TaskStatus.PENDING.value,
        filename=file.filename,
        investigation_question=normalized_question,
        created_at=datetime.now(timezone.utc)
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
        "status": TaskStatus.PENDING.value,
        "investigation_question": normalized_question,
    }


@router.post("/investigate/")
async def investigate(
    background_tasks: BackgroundTasks,
    primary_file: UploadFile = File(...),
    secondary_files: list[UploadFile] | None = File(None),
    investigation_question: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Investigate a primary dataset with optional secondary datasets.

    Runs the full pipeline on the primary file and cross-dataset analysis
    if secondary files are provided (Phase 9).
    """
    normalized_question = _normalize_investigation_question(
        investigation_question
    )
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
        investigation_question=normalized_question,
        created_at=datetime.now(timezone.utc),
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
        "investigation_question": normalized_question,
    }
