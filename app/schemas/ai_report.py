"""Schemas for AI-generated investigation narratives.

This module defines the output structure for LLM-generated content
that wraps — but does not modify — the deterministic InvestigationReport.

Separation of concerns:
- InvestigationReport: deterministic pipeline output (signals → evidence →
  hypotheses → findings)
- Narrative: LLM-generated natural language (executive summary, findings,
  evidence, business impact, recommendations)
- AIInvestigationReport: wraps both together with model metadata for
  traceability
"""

from datetime import datetime
from pydantic import BaseModel

from app.schemas.investigation_report import InvestigationReport
from app.schemas.interactive import InteractiveInvestigationReport


# ---------------------------------------------------------------------------
# Narrative — the structured output every NarrativeGenerator must produce
# ---------------------------------------------------------------------------

class Narrative(BaseModel):
    """LLM-generated investigation narrative.

    This is the target output structure for EVERY NarrativeGenerator
    implementation (mock, anthropic, openai, etc.).  Prompts are designed
    around this structure; changing it means changing the prompt contract.
    """

    executive_summary: str
    """High-level synthesis: what was investigated, key conclusions,
    overall risk assessment, and confidence level."""

    key_findings: list[str]
    """One entry per supported or refuted hypothesis, ranked by confidence.
    Each finding states the claim, the verdict (supported / refuted), and
    the strength of evidence."""

    supporting_evidence_summary: str
    """Narrative summary of the evidence backing the key findings.
    References specific metrics and values where available so the reader
    can trace claims back to data."""

    business_impact_summary: str
    """Why the findings matter to the business.  Describes risks,
    opportunities, and materiality of confirmed patterns."""

    recommendations: list[str]
    """Prioritised, actionable next steps.  Each recommendation should
    reference the finding it addresses."""


# ---------------------------------------------------------------------------
# ModelMetadata — traceability for generative outputs
# ---------------------------------------------------------------------------

class ModelMetadata(BaseModel):
    """Metadata about the model and prompt that produced a Narrative.

    Storing this alongside the output makes it possible to:
    - audit which model / prompt version produced a given report
    - compare outputs across providers
    - detect when a report needs regeneration after a prompt update
    """

    provider: str
    """Provider identifier: 'mock', 'anthropic', 'openai', etc."""

    model_name: str
    """Name of the specific model used, e.g. 'claude-sonnet-5', 'mock-0'."""

    prompt_version: str
    """Semver of the prompt contract used, e.g. '1.0.0'."""

    generated_at: datetime
    """UTC timestamp of generation."""


# ---------------------------------------------------------------------------
# AIInvestigationReport — the top-level output
# ---------------------------------------------------------------------------

class AIInvestigationReport(BaseModel):
    """Wraps the deterministic InvestigationReport with an AI-generated
    Narrative and provenance metadata.

    Key design choice: this WRAPS rather than EXTENDS InvestigationReport.
    The deterministic report is untouched — it remains a pure product of
    the statistical pipeline.  Generative outputs live alongside it, not
    inside it.

    This separation:
    - keeps deterministic and generative outputs independently testable
    - makes multi-model comparison easy (swap the narrative, same report)
    - allows the system to operate without an LLM (narrative is optional)
    """

    investigation_report: InvestigationReport
    """The deterministic pipeline output: signals → evidence → hypotheses →
    validated findings.  Always present, never modified by an LLM."""

    narrative: Narrative | None = None
    """LLM-generated natural language narrative.  None when LLM integration
    is disabled or unavailable."""

    model_metadata: ModelMetadata | None = None
    """Provenance information for the narrative.  None when narrative is
    produced without a model (e.g., a mock that returns empty strings)."""

    interactive_investigation: InteractiveInvestigationReport | None = None
    """Forward-looking interactive investigation output (Phase 8).
    Follow-up questions, data gaps, guided investigation paths, and
    unresolved areas.  Produced deterministically — no LLM required."""
