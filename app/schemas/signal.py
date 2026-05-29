from pydantic import BaseModel
from app.models.enums import SignalType, SignalSeverity

class Signal(BaseModel):
    type: SignalType
    severity: SignalSeverity
    column: str | None = None
    message: str


class SignalReport(BaseModel):
    signals: list[Signal]