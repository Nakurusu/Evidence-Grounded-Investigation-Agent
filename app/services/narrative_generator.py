"""Narrative generation — provider-agnostic interface + implementations.

This module defines the NarrativeGenerator Protocol that every provider
must implement, plus a MockNarrativeGenerator for development and testing.

Architecture
------------
The pipeline depends on the NarrativeGenerator PROTOCOL, never on a
concrete provider.  This means:

    pipeline.py:
        generator: NarrativeGenerator = get_narrative_generator()
        narrative, metadata = generator.generate(report)

    Never:
        generator = AnthropicNarrativeGenerator()  # <-- hard dependency

Adding a new provider requires:
1.  Implement NarrativeGenerator.
2.  Register it in the factory function.
3.  Set the config value.

The pipeline never changes.
"""

from datetime import datetime, UTC
from typing import Protocol

from app.schemas.investigation_report import InvestigationReport
from app.schemas.ai_report import Narrative, ModelMetadata


# ---------------------------------------------------------------------------
# Protocol — the contract every provider must satisfy
# ---------------------------------------------------------------------------


class NarrativeGenerator(Protocol):
    """Provider-agnostic interface for generating investigation narratives.

    Each implementation accepts an InvestigationReport (deterministic
    pipeline output) and returns a Narrative with provider metadata.

    The pipeline depends on this Protocol.  Concrete implementations are
    resolved at startup via configuration — the pipeline never imports
    a specific provider directly.
    """

    def generate(
        self,
        report: InvestigationReport,
    ) -> tuple[Narrative, ModelMetadata]:
        """Generate a narrative from a deterministic investigation report.

        Args:
            report:  The complete pipeline output (findings, evidence,
                     executive summary, next steps).

        Returns:
            A (Narrative, ModelMetadata) pair.  The Narrative contains
            the structured natural-language sections; the ModelMetadata
            records which provider, model, and prompt version produced it.
        """
        ...


# ---------------------------------------------------------------------------
# Mock — deterministic composition, no LLM calls
# ---------------------------------------------------------------------------


class MockNarrativeGenerator:
    """Deterministic mock that composes narratives from structured data.

    Produces a valid Narrative WITHOUT calling any LLM.  It uses:
    - Finding titles and statuses for key findings
    - Evidence metric names and values for the evidence summary
    - Report next_steps for recommendations
    - Executive summary fields for the narrative summary

    This is useful for:
    - Testing the prompt contract and pipeline integration
    - Running the system without LLM credentials
    - Establishing baseline output quality before introducing LLMs
    """

    PROVIDER = "mock"
    MODEL_NAME = "mock-0"

    def generate(
        self,
        report: InvestigationReport,
    ) -> tuple[Narrative, ModelMetadata]:
        es = report.executive_summary

        # -- Executive Summary -------------------------------------------------
        executive_summary = (
            f"Investigation complete.  {es.total_hypotheses} hypotheses "
            f"were tested: {es.supported_count} supported, "
            f"{es.refuted_count} refuted, {es.inconclusive_count} "
            f"inconclusive.  Overall risk is assessed as **{es.overall_risk}** "
            f"with **{es.overall_confidence}** confidence."
        )

        # -- Key Findings ------------------------------------------------------
        key_findings = [
            f"[{f.status.value.upper()}] {f.title} "
            f"(confidence: {f.confidence.value})"
            for f in report.findings
        ]

        # -- Supporting Evidence -----------------------------------------------
        evidence_parts: list[str] = []
        for f in report.findings:
            for e in f.supporting_evidence:
                if e.metric and e.value is not None:
                    evidence_parts.append(
                        f"{e.metric}={e.value} ({e.title})"
                    )
                else:
                    evidence_parts.append(e.title)
        supporting_evidence_summary = (
            "Evidence collected across findings:\n- "
            + "\n- ".join(evidence_parts)
            if evidence_parts
            else "No supporting evidence was collected."
        )

        # -- Business Impact ---------------------------------------------------
        high_findings = [
            f for f in report.findings
            if f.confidence.value == "high" and f.status.value == "supported"
        ]
        if high_findings:
            titles = ", ".join(f"'{f.title}'" for f in high_findings)
            business_impact_summary = (
                f"High-priority findings requiring attention: {titles}.  "
                f"These represent the most significant confirmed risks "
                f"and opportunities in the dataset."
            )
        elif es.supported_count > 0:
            business_impact_summary = (
                f"{es.supported_count} hypotheses were supported by "
                f"evidence.  These findings should be reviewed for "
                f"business impact."
            )
        else:
            business_impact_summary = (
                "No hypotheses were confirmed.  Consider collecting "
                "additional data to strengthen the investigation."
            )

        # -- Recommendations ---------------------------------------------------
        recommendations = report.next_steps[:5] if report.next_steps else [
            "Review the investigation findings with domain experts.",
            "Collect additional data for inconclusive hypotheses.",
        ]

        narrative = Narrative(
            executive_summary=executive_summary,
            key_findings=key_findings,
            supporting_evidence_summary=supporting_evidence_summary,
            business_impact_summary=business_impact_summary,
            recommendations=recommendations,
        )

        metadata = ModelMetadata(
            provider=self.PROVIDER,
            model_name=self.MODEL_NAME,
            prompt_version="1.0.0",
            generated_at=datetime.now(UTC),
        )

        return narrative, metadata


# ---------------------------------------------------------------------------
# Factory — resolves the configured provider
# ---------------------------------------------------------------------------


def get_narrative_generator() -> NarrativeGenerator:
    """Return a NarrativeGenerator based on application settings.

    Reads LLM_MODE from settings:
    - "mock" (or unset) → MockNarrativeGenerator (deterministic)
    - "openai"          → LLMNarrativeGenerator (OpenAI-compatible API)

    Returns:
        A NarrativeGenerator implementation.
    """
    from app.core.settings import settings  # local import — avoid coupling

    mode = getattr(settings, "LLM_MODE", "mock") or "mock"

    if mode == "mock":
        return MockNarrativeGenerator()

    if mode == "openai":
        api_key = getattr(settings, "LLM_API_KEY", "")
        if not api_key:
            raise ValueError(
                "LLM_MODE='openai' requires LLM_API_KEY to be set "
                "in .env or environment variables."
            )
        from app.services.llm_narrative_generator import LLMNarrativeGenerator

        return LLMNarrativeGenerator(
            api_key=api_key,
            base_url=getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1"),
            model=getattr(settings, "LLM_MODEL", "gpt-4o"),
        )

    raise ValueError(
        f"Unknown LLM_MODE '{mode}'.  Supported modes: mock, openai"
    )
