from fastapi import FastAPI
from api.upload import router as upload_router
from api.task import router as task_router

app = FastAPI()

app.include_router(upload_router)
app.include_router(task_router)