from pydantic import BaseModel
from app.models.enums import SignalType

class Evidence(BaseModel):
    title: str
    description: str

    metric: str | None = None
    value: str | float | int | None = None

    supporting_signal: SignalType | None = None
    related_column: str | None = None
    method: str | None = None
    threshold: str | float | int | None = None
    sample_size: int | None = None
    direction: str | None = None
    strength: str | None = None
    limitation: str | None = None


class EvidenceReport(BaseModel):
    evidence: list[Evidence]
