from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict
from app.models.enums import TaskStatus


class TaskProgress(BaseModel):
    current_stage: str | None = None
    completed_stages: list[str] = []
    percent: int | None = None
    stage_detail: str | None = None
    failed_stage: str | None = None
    stage_title: str | None = None
    stage_goal: str | None = None
    stage_input: str | None = None
    stage_output: str | None = None
    stage_reason: str | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: UUID
    status: TaskStatus
    filename: str
    investigation_question: str | None = None
    created_at: datetime
    finished_at: datetime | None
    result: dict | None
    error_message: str | None = None
    current_stage: str | None = None
    progress: TaskProgress | dict | None = None
