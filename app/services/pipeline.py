from services.parser import parse_file
from services.normalizer import normalize_products
from services.analyzer import generate_sales_summary
from services.validator import validate_columns
from services.task_store import TASK_RESULTS

def process_uploaded_file(task_id, file):

    df = parse_file(file)

    validate_columns(df)

    df = normalize_products(df)

    summary = generate_sales_summary(df)

    TASK_RESULTS[task_id] = {
        "status": "completed",
        "summary": summary
    }