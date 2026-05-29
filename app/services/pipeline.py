from app.services.parser import parse_file
from app.services.normalizer import normalize_dataframe
from app.services.analyzer import generate_sales_summary
from app.services.validator import validate_dataframe
from datetime import datetime, UTC
from app.db.database import SessionLocal
from app.models.task import Task
from app.core.logger import logger
from app.models.enums import TaskStatus
from app.services.profiler import profile_dataframe
from app.services.quality import assess_data_quality

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
        df = normalize_dataframe(df)
        validate_dataframe(df)
        profile = profile_dataframe(df)
        logger.info(profile.model_dump())
        quality_report = assess_data_quality(df)
        logger.info(quality_report.model_dump())
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