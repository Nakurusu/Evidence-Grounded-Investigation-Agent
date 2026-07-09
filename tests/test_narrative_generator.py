"""Tests for app/services/narrative_generator.py."""

import pytest
from app.services.narrative_generator import (
    MockNarrativeGenerator,
    get_narrative_generator,
)
from app.schemas.ai_report import Narrative, ModelMetadata, AIInvestigationReport
from app.schemas.investigation_report import (
    InvestigationReport,
    ExecutiveSummary,
    DatasetSummary,
    Finding,
)
from app.models.enums import HypothesisStatus, HypothesisConfidence


def _minimal_report(
    supported: int = 2,
    refuted: int = 1,
    inconclusive: int = 0,
) -> InvestigationReport:
    findings = []
    for i in range(supported):
        findings.append(Finding(
            title=f"Supported finding {i}",
            observation=f"Observation {i}",
            status=HypothesisStatus.SUPPORTED,
            confidence=HypothesisConfidence.HIGH if i == 0 else HypothesisConfidence.MEDIUM,
            supporting_evidence=[],
            contradicting_evidence=[],
            analysis=f"Analysis {i}",
            business_impact=f"Impact {i}",
            recommendation=f"Recommendation {i}",
        ))
    for i in range(refuted):
        findings.append(Finding(
            title=f"Refuted finding {i}",
            observation=f"Refuted obs {i}",
            status=HypothesisStatus.REFUTED,
            confidence=HypothesisConfidence.LOW,
            supporting_evidence=[],
            contradicting_evidence=[],
            analysis=f"Analysis {i}",
            business_impact=f"Impact {i}",
            recommendation=f"Rec {i}",
        ))
    for i in range(inconclusive):
        findings.append(Finding(
            title=f"Inconclusive finding {i}",
            observation=f"Inconclusive obs {i}",
            status=HypothesisStatus.INCONCLUSIVE,
            confidence=HypothesisConfidence.LOW,
            supporting_evidence=[],
            contradicting_evidence=[],
            analysis=f"Analysis {i}",
            business_impact=f"Impact {i}",
            recommendation=f"Rec {i}",
        ))

    es = ExecutiveSummary(
        total_hypotheses=supported + refuted + inconclusive,
        supported_count=supported,
        refuted_count=refuted,
        inconclusive_count=inconclusive,
        highest_priority_findings=[f"Supported finding 0"] if supported > 0 else [],
        overall_risk="medium",
        overall_confidence="high" if supported > refuted else "low",
    )
    ds = DatasetSummary(
        row_count=100, column_count=5,
        numeric_columns=["revenue"], categorical_columns=["region"],
        datetime_columns=["date"], text_columns=[], boolean_columns=[],
    )
    return InvestigationReport(
        executive_summary=es,
        dataset_summary=ds,
        findings=findings,
        next_steps=["Step 1", "Step 2", "Step 3"],
    )


class TestMockNarrativeGenerator:
    def test_returns_narrative_and_metadata(self):
        gen = MockNarrativeGenerator()
        narrative, metadata = gen.generate(_minimal_report())
        assert isinstance(narrative, Narrative)
        assert isinstance(metadata, ModelMetadata)

    def test_narrative_has_all_fields(self):
        gen = MockNarrativeGenerator()
        narrative, _ = gen.generate(_minimal_report())
        assert len(narrative.executive_summary) > 0
        assert len(narrative.key_findings) > 0
        assert len(narrative.supporting_evidence_summary) > 0
        assert len(narrative.business_impact_summary) > 0
        assert len(narrative.recommendations) > 0

    def test_key_findings_match_report(self):
        gen = MockNarrativeGenerator()
        narrative, _ = gen.generate(_minimal_report(supported=3, refuted=0, inconclusive=0))
        assert len(narrative.key_findings) == 3

    def test_metadata_is_mock(self):
        gen = MockNarrativeGenerator()
        _, metadata = gen.generate(_minimal_report())
        assert metadata.provider == "mock"
        assert metadata.model_name == "mock-0"
        assert metadata.prompt_version == "1.0.0"

    def test_recommendations_capped_at_5(self):
        """Long next_steps list should be trimmed."""
        report = _minimal_report()
        report.next_steps = [f"Step {i}" for i in range(10)]
        gen = MockNarrativeGenerator()
        narrative, _ = gen.generate(report)
        assert len(narrative.recommendations) == 5

    def test_high_confidence_findings_in_impact(self):
        gen = MockNarrativeGenerator()
        narrative, _ = gen.generate(_minimal_report(supported=2, refuted=0, inconclusive=0))
        # The first finding has HIGH confidence
        assert "Supported finding 0" in narrative.business_impact_summary

    def test_all_supported_report(self):
        gen = MockNarrativeGenerator()
        narrative, _ = gen.generate(_minimal_report(supported=3, refuted=0, inconclusive=0))
        assert "3 hypotheses were tested" in narrative.executive_summary
        assert "3 supported" in narrative.executive_summary

    def test_returns_valid_wrapped_report(self):
        gen = MockNarrativeGenerator()
        report = _minimal_report()
        narrative, metadata = gen.generate(report)
        ai_report = AIInvestigationReport(
            investigation_report=report,
            narrative=narrative,
            model_metadata=metadata,
        )
        d = ai_report.model_dump()
        assert d["narrative"] is not None
        assert d["model_metadata"] is not None


class TestFactory:
    def test_default_returns_mock(self):
        gen = get_narrative_generator()
        assert isinstance(gen, MockNarrativeGenerator)

    def test_factory_returns_mock(self):
        """Factory should return MockNarrativeGenerator with default settings."""
        gen = get_narrative_generator()
        assert gen is not None
        # With default LLM_MODE="mock" or unset, returns MockNarrativeGenerator
        narrative, metadata = gen.generate(_minimal_report())
        assert metadata.provider == "mock"
