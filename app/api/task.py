from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.task import Task
from app.schemas.task import TaskResponse
from app.schemas.ai_report import AIInvestigationReport
from app.schemas.interactive import DrillDownResult
from app.services.drilldown import DrillDownService
from app.services.file_manager import get_uploaded_file_path
from app.services.normalizer import normalize_dataframe
from app.services.parser import parse_file

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


@router.post(
    "/{task_id}/follow-ups/{question_index}/drilldown",
    response_model=DrillDownResult,
)
async def run_follow_up_drilldown(
    task_id: str,
    question_index: int,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )
    if not task.result:
        raise HTTPException(
            status_code=400,
            detail="Task has no investigation result",
        )

    try:
        report = AIInvestigationReport.model_validate(task.result)
        file_path = get_uploaded_file_path(task_id, task.filename)
        df = normalize_dataframe(parse_file(file_path))
        result = DrillDownService().run(df, report, question_index)
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if report.interactive_investigation is None:
        raise HTTPException(
            status_code=400,
            detail="Task has no interactive investigation result",
        )

    report.interactive_investigation.drilldown_steps.append(result)
    task.result = report.model_dump(mode="json")
    db.commit()
    db.refresh(task)

    return result
