from pydantic import BaseModel

from app.models.enums import HypothesisStatus, HypothesisConfidence
from app.schemas.hypothesis import Hypothesis
from app.schemas.evidence import Evidence


class ValidatedHypothesis(BaseModel):
    hypothesis: Hypothesis
    status: HypothesisStatus
    supporting_evidence: list[Evidence]
    contradicting_evidence: list[Evidence]
    adjusted_confidence: HypothesisConfidence


class ValidationReport(BaseModel):
    validated: list[ValidatedHypothesis]
