from pydantic import BaseModel, Field

from app.models.enums import HypothesisStatus, HypothesisConfidence
from app.schemas.evidence import Evidence


class ExecutiveSummary(BaseModel):
    investigation_question: str | None = None
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
    metric_columns: list[str] = Field(default_factory=list)
    dimension_columns: list[str] = Field(default_factory=list)
    time_columns: list[str] = Field(default_factory=list)
    entity_columns: list[str] = Field(default_factory=list)
    identifier_columns: list[str] = Field(default_factory=list)


class QualitySummary(BaseModel):
    issue_count: int = 0
    risk_level: str = "low"
    warnings: list[str] = Field(default_factory=list)


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
    primary_signal_type: str | None = None
    affected_columns: list[str] = Field(default_factory=list)
    key_metrics: dict[str, float | int | str] = Field(default_factory=dict)
    trace: dict[str, list[str] | str] = Field(default_factory=dict)
    evidence_strength: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class CauseCandidate(BaseModel):
    title: str
    explanation: str
    score: float
    confidence: HypothesisConfidence
    related_columns: list[str] = Field(default_factory=list)
    supporting_finding_titles: list[str] = Field(default_factory=list)
    supporting_evidence_titles: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_validation_step: str


class InvestigationReport(BaseModel):
    executive_summary: ExecutiveSummary
    dataset_summary: DatasetSummary
    findings: list[Finding]
    cause_candidates: list[CauseCandidate] = Field(default_factory=list)
    next_steps: list[str]
    quality_summary: QualitySummary | None = None
