from services.parser import parse_file
from services.normalizer import normalize_products
from services.analyzer import generate_sales_summary
from services.validator import validate_columns
from datetime import datetime, UTC
from db.database import SessionLocal
from models.task import Task

def process_uploaded_file(task_id, file):

    db = SessionLocal()
    task = db.get(Task, task_id)

    try:
        df = parse_file(file)
        validate_columns(df)
        df = normalize_products(df)
        summary = generate_sales_summary(df)
        task.status = "completed"
        task.result = summary
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()