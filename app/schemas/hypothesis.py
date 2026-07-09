from pydantic import BaseModel
from app.models.enums import HypothesisConfidence, SignalType

class Hypothesis(BaseModel):
    title: str
    confidence: HypothesisConfidence
    supporting_signals: list[SignalType]
    description: str
    is_composite: bool = False
    related_columns: list[str] = []

class HypothesisReport(BaseModel):
    hypotheses: list[Hypothesis]