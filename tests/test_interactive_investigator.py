"""Tests for app/services/interactive_investigator.py."""

import pytest
from app.services.interactive_investigator import InteractiveInvestigator
from app.schemas.interactive import (
    InteractiveInvestigationReport,
    FollowUpQuestion,
    DataGap,
    InvestigationPath,
)
from app.schemas.investigation_report import (
    InvestigationReport,
    ExecutiveSummary,
    DatasetSummary,
    Finding,
)
from app.schemas.evidence import Evidence
from app.models.enums import SignalType, HypothesisStatus, HypothesisConfidence


def _finding(
    title: str = "test finding",
    status: HypothesisStatus = HypothesisStatus.SUPPORTED,
    confidence: HypothesisConfidence = HypothesisConfidence.HIGH,
    signal_type: SignalType = SignalType.OUTLIER_DETECTED,
    column: str = "revenue",
) -> Finding:
    return Finding(
        title=title,
        observation=f"Observation for {title}",
        status=status,
        confidence=confidence,
        supporting_evidence=[
            Evidence(
                title="Test evidence",
                description="test",
                metric="outlier_count",
                value=5,
                supporting_signal=signal_type,
                related_column=column,
            )
        ],
        contradicting_evidence=[],
        analysis=f"Analysis for {title}",
        business_impact=f"Impact for {title}",
        recommendation=f"Recommendation for {title}",
    )


def _report(findings: list[Finding]) -> InvestigationReport:
    supported = sum(1 for f in findings if f.status == HypothesisStatus.SUPPORTED)
    refuted = sum(1 for f in findings if f.status == HypothesisStatus.REFUTED)
    inconclusive = sum(1 for f in findings if f.status == HypothesisStatus.INCONCLUSIVE)
    return InvestigationReport(
        executive_summary=ExecutiveSummary(
            total_hypotheses=len(findings),
            supported_count=supported,
            refuted_count=refuted,
            inconclusive_count=inconclusive,
            highest_priority_findings=[
                f.title for f in findings if f.confidence == HypothesisConfidence.HIGH
            ][:3],
            overall_risk="medium",
            overall_confidence="high",
        ),
        dataset_summary=DatasetSummary(
            row_count=100, column_count=5,
            numeric_columns=["revenue"], categorical_columns=["region"],
            datetime_columns=["date"], text_columns=[], boolean_columns=[],
        ),
        findings=findings,
        next_steps=["Investigate further", "Collect more data"],
    )


class TestInteractiveInvestigator:
    def test_returns_interactive_report(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding()])
        result = investigator.investigate(report)
        assert isinstance(result, InteractiveInvestigationReport)

    def test_all_sections_present(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding()])
        result = investigator.investigate(report)
        assert len(result.follow_up_questions) > 0
        assert len(result.investigation_paths) >= 0
        # data_gaps and unresolved may be empty depending on finding

    def test_follow_up_questions_have_valid_structure(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding()])
        result = investigator.investigate(report)
        for q in result.follow_up_questions:
            assert len(q.question) > 0
            assert q.priority in ("high", "medium", "low")
            assert q.category in (
                "drill_down", "data_gap",
                "alternative_explanation", "cross_pattern",
            )
            assert len(q.related_finding_titles) >= 1

    def test_investigation_path_has_steps(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding(status=HypothesisStatus.SUPPORTED)])
        result = investigator.investigate(report)
        for p in result.investigation_paths:
            assert len(p.title) > 0
            assert len(p.description) > 0
            assert len(p.steps) > 0
            assert len(p.starting_finding) > 0

    def test_paths_limited_to_5(self):
        """More than 5 supported findings → paths capped at 5."""
        findings = [
            _finding(title=f"finding_{i}", signal_type=SignalType.OUTLIER_DETECTED)
            for i in range(8)
        ]
        investigator = InteractiveInvestigator()
        report = _report(findings)
        result = investigator.investigate(report)
        assert len(result.investigation_paths) <= 5

    def test_inconclusive_areas_tracked(self):
        findings = [
            _finding("f1", status=HypothesisStatus.SUPPORTED),
            _finding("f2", status=HypothesisStatus.INCONCLUSIVE),
            _finding("f3", status=HypothesisStatus.INCONCLUSIVE),
        ]
        investigator = InteractiveInvestigator()
        report = _report(findings)
        result = investigator.investigate(report)
        assert len(result.unresolved_areas) == 2
        assert "f2" in result.unresolved_areas
        assert "f3" in result.unresolved_areas

    def test_empty_findings_does_not_crash(self):
        investigator = InteractiveInvestigator()
        report = _report([])
        result = investigator.investigate(report)
        assert len(result.follow_up_questions) == 0
        assert len(result.investigation_paths) == 0

    def test_data_gaps_have_sources(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding()])
        result = investigator.investigate(report)
        for g in result.data_gaps:
            assert len(g.gap) > 0
            assert len(g.impact) > 0
            assert len(g.suggested_source) > 0
            assert len(g.affected_hypotheses) >= 1

    def test_cross_pattern_detected_for_multiple_signals(self):
        """When outlier + right_skewed co-occur, cross-pattern questions appear."""
        findings = [
            _finding("outlier", signal_type=SignalType.OUTLIER_DETECTED),
            _finding("skew", signal_type=SignalType.RIGHT_SKEWED),
        ]
        investigator = InteractiveInvestigator()
        report = _report(findings)
        result = investigator.investigate(report)
        cross = [q for q in result.follow_up_questions if q.category == "cross_pattern"]
        assert len(cross) >= 1

    def test_refuted_finding_generates_alternative(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding("refuted", status=HypothesisStatus.REFUTED)])
        result = investigator.investigate(report)
        alt = [q for q in result.follow_up_questions if q.category == "alternative_explanation"]
        assert len(alt) >= 1

    def test_deduplication(self):
        """Identical questions should not be duplicated."""
        findings = [
            _finding("f1", signal_type=SignalType.OUTLIER_DETECTED),
            _finding("f2", signal_type=SignalType.OUTLIER_DETECTED),
        ]
        investigator = InteractiveInvestigator()
        report = _report(findings)
        result = investigator.investigate(report)
        questions = [q.question for q in result.follow_up_questions]
        assert len(questions) == len(set(questions))

    def test_result_is_serializable(self):
        investigator = InteractiveInvestigator()
        report = _report([_finding()])
        result = investigator.investigate(report)
        d = result.model_dump()
        assert "follow_up_questions" in d
        assert "data_gaps" in d
        assert "investigation_paths" in d
        assert "unresolved_areas" in d
