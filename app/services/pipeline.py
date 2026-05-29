from app.services.parser import parse_file
from app.services.normalizer import normalize_products
from app.services.analyzer import generate_sales_summary
from app.services.validator import validate_columns
from datetime import datetime, UTC
from app.db.database import SessionLocal
from app.models.task import Task
from app.core.logger import logger
from app.models.enums import TaskStatus
from app.services.profiler import profile_dataframe

def process_uploaded_file(task_id, file):

    db = SessionLocal()
    task = db.get(Task, task_id)

    try:
        logger.info(
            f"processing task {task_id}"
        )
        task.status = TaskStatus.PROCESSING.value
        df = parse_file(file)
        logger.info(
            f"parsed file for task {task_id}"
        )
        profile = profile_dataframe(df)
        logger.info(profile.model_dump())
        validate_columns(df)
        df = normalize_products(df)
        summary = generate_sales_summary(df)
        logger.info(
            f"completed task {task_id}"
        )
        task.status = TaskStatus.COMPLETED.value
        task.result = summary
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(
            f"task failed: {task_id}"
        )
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()