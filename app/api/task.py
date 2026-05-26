from fastapi import APIRouter
from services.task_store import TASK_RESULTS

router = APIRouter(
    prefix="/task",
    tags=["task"]
)

@router.get("/{task_id}")
async def get_task(task_id: str):

    result = TASK_RESULTS.get(task_id)

    if not result:
        return {"error": "Task not found"}

    return {
        "task_id": task_id,
        "result": result
    }