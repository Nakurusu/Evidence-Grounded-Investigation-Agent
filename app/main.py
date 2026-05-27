from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.task import router as task_router

app = FastAPI()

app.include_router(upload_router)
app.include_router(task_router)