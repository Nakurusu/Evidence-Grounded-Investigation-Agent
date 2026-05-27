from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.dependencies import get_db
from models.task import Task
from schemas.task import TaskResponse

router = APIRouter(
    prefix="/task",
    tags=["task"]
)

@router.get(
        "/{task_id}"
        ,response_model=TaskResponse
        )
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):

    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404, 
            detail="Task not found"
        )

    return task