from pydantic import BaseModel, Field
from app.models.enums import SignalType, SignalSeverity

class Signal(BaseModel):
    type: SignalType
    severity: SignalSeverity
    column: str | None = None
    message: str
    metric_column: str | None = None
    dimension_column: str | None = None
    statistics: dict[str, float | int | str] = Field(default_factory=dict)


class SignalReport(BaseModel):
    signals: list[Signal]
