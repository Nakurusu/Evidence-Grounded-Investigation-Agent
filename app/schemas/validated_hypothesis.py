from pydantic import BaseModel

from app.models.enums import HypothesisStatus, HypothesisConfidence
from app.schemas.hypothesis import Hypothesis
from app.schemas.evidence import Evidence


class ValidatedHypothesis(BaseModel):
    hypothesis: Hypothesis
    status: HypothesisStatus
    supporting_evidence: list[Evidence]
    contradicting_evidence: list[Evidence]
    neutral_evidence: list[Evidence] = []
    adjusted_confidence: HypothesisConfidence


class Finding(BaseModel):
    """A self-contained summary of one validated hypothesis, ready for LLM consumption."""
    hypothesis_title: str
    status: HypothesisStatus
    summary: str
    supporting_metrics: dict[str, float]
    contradicting_metrics: dict[str, float]


class ValidatedHypothesisReport(BaseModel):
    validated: list[ValidatedHypothesis]
    findings: list[Finding]
