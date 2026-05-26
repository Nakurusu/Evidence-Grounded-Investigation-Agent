from fastapi import APIRouter, UploadFile
from services.parser import parse_file

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile):

    df = parse_file(file)

    return {
        "filename": file.filename,
        "columns": df.columns.tolist(),
        "rows": len(df)
    }