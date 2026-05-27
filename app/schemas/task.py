from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict

class TaskResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: UUID
    status: str
    filename: str
    created_at: datetime
    finished_at: datetime | None
    result: dict | None
    error: str | None