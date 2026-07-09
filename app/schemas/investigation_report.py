from pydantic import BaseModel

from app.models.enums import HypothesisStatus, HypothesisConfidence
from app.schemas.evidence import Evidence


class ExecutiveSummary(BaseModel):
    total_hypotheses: int
    supported_count: int
    refuted_count: int
    inconclusive_count: int
    highest_priority_findings: list[str]
    overall_risk: str
    overall_confidence: str


class DatasetSummary(BaseModel):
    row_count: int
    column_count: int
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    text_columns: list[str]
    boolean_columns: list[str]


class Finding(BaseModel):
    title: str
    observation: str
    status: HypothesisStatus
    confidence: HypothesisConfidence
    supporting_evidence: list[Evidence]
    contradicting_evidence: list[Evidence]
    analysis: str
    business_impact: str
    recommendation: str


class InvestigationReport(BaseModel):
    executive_summary: ExecutiveSummary
    dataset_summary: DatasetSummary
    findings: list[Finding]
    next_steps: list[str]
