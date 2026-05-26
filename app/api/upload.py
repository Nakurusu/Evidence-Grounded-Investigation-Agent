from fastapi import APIRouter, UploadFile
from services.parser import parse_file
from services.normalizer import normalize_products
from services.analyzer import generate_sales_summary

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile):

    df = parse_file(file)
    df = normalize_products(df)
    summary = generate_sales_summary(df)

    return {
        "summary": summary
    }