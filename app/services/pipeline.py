from services.parser import parse_file
from services.normalizer import normalize_products
from services.analyzer import generate_sales_summary
from services.validator import validate_columns
from datetime import datetime, UTC
from db.database import SessionLocal
from models.task import Task
from core.logger import logger
def process_uploaded_file(task_id, file):

    db = SessionLocal()
    task = db.get(Task, task_id)

    try:
        logger.info(
            f"processing task {task_id}"
        )
        df = parse_file(file)
        logger.info(
            f"parsed file for task {task_id}"
        )
        validate_columns(df)
        df = normalize_products(df)
        summary = generate_sales_summary(df)
        logger.info(
            f"completed task {task_id}"
        )
        task.status = "completed"
        task.result = summary
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(
            f"task failed: {task_id}"
        )
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()