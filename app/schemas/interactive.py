"""Schemas for interactive investigation — Phase 8.

These schemas define the output of the interactive investigation engine:
follow-up questions, data gaps, investigation paths, and unresolved areas.

They sit alongside the deterministic InvestigationReport and the LLM
Narrative as the third output layer of the investigation pipeline.

Architecture note:
    InvestigationReport  →  Narrative  →  InteractiveInvestigationReport
    (deterministic)         (generative)    (forward-looking)
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DrillDownEvidence(BaseModel):
    """A compact evidence item produced by a runnable follow-up analysis."""

    label: str
    value: float | int | str | None
    description: str


class DrillDownResult(BaseModel):
    """Result of executing a runnable follow-up question.

    Drill-down results are appended to the interactive investigation layer.
    They do not modify the original deterministic InvestigationReport.
    """

    step_id: str
    question: str
    status: str
    analysis_type: str
    summary: str
    related_columns: list[str] = Field(default_factory=list)
    evidence: list[DrillDownEvidence] = Field(default_factory=list)
    sample_records: list[dict[str, object | None]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime


class FollowUpQuestion(BaseModel):
    """A question the analyst should investigate next.

    Each question is categorized so the user understands what kind of
    exploration it represents and what data (if any) is needed to answer it.
    """

    question: str
    """The natural-language question, e.g. 'Which specific products are
    driving the revenue concentration?'"""

    priority: str
    """'high', 'medium', or 'low' — derived from the parent finding's
    confidence and status."""

    category: str
    """The type of follow-up exploration:
    - 'drill_down':              go deeper into a confirmed finding
    - 'data_gap':                can only be answered with additional data
    - 'alternative_explanation': explore alternative causes for a refuted
                                  hypothesis
    - 'cross_pattern':           spans multiple findings / signal types
    """

    related_finding_titles: list[str]
    """Which findings in the InvestigationReport motivate this question."""

    required_data: list[str] = []
    """Additional data dimensions, sources, or columns that would help
    answer this question.  Empty if the existing data is sufficient."""


class DataGap(BaseModel):
    """A gap in the available data that limits investigation confidence.

    Data gaps are different from missing values in the existing dataset.
    They describe data the analyst does NOT have but WOULD NEED to make
    stronger conclusions.
    """

    gap: str
    """Short description of what is missing, e.g.
    'Customer demographic data (age, segment, tenure)'."""

    impact: str
    """Why this gap matters — which conclusions are weakened without it."""

    affected_hypotheses: list[str]
    """Hypothesis titles that could be resolved more confidently with this
    data."""

    suggested_source: str
    """Where this data might be obtained, e.g. 'CRM system', 'marketing
    platform', 'inventory database', 'external benchmark'."""


class InvestigationPath(BaseModel):
    """A guided exploration path — a sequence of steps the analyst can follow
    to investigate a finding further.

    Each path starts from a confirmed finding and walks through progressively
    deeper analysis, similar to what an experienced analyst would do.
    """

    title: str
    """Short label, e.g. 'Investigate revenue concentration by customer segment'."""

    description: str
    """What this path explores and why it matters."""

    steps: list[str]
    """Ordered, actionable steps.  Each step should be specific enough to
    execute without further guidance, e.g.:
    1. Segment revenue by customer size decile.
    2. Calculate share of revenue from top 3 customers per region.
    3. Compare concentration trends over the last 4 quarters.
    """

    starting_finding: str
    """The finding title this path originates from."""


class InteractiveInvestigationReport(BaseModel):
    """The forward-looking output of the interactive investigation engine.

    Produced after the deterministic report and narrative.  Helps the
    analyst answer: "What should I investigate next?"

    Consumed by:
    - The API layer (to present follow-up options to the user)
    - Future interactive UI (to render guided investigation workflows)
    - Future LLM agents (to plan multi-step investigations)
    """

    follow_up_questions: list[FollowUpQuestion]
    """Prioritised questions the analyst should explore next."""

    data_gaps: list[DataGap]
    """Additional data that would strengthen the investigation."""

    investigation_paths: list[InvestigationPath]
    """Guided, step-by-step exploration paths for key findings."""

    unresolved_areas: list[str]
    """Hypothesis titles that remain INCONCLUSIVE and need more data or
    analysis to resolve."""

    drilldown_steps: list[DrillDownResult] = Field(default_factory=list)
    """Executed follow-up analyses appended after the original report.
    These are investigation steps, not replacements for the initial findings."""
