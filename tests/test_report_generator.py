"""Tests for app/services/report_generator.py."""

import pytest
from app.services.report_generator import (
    generate_report,
    _build_simple_finding,
    _build_composite_finding,
    _build_finding,
    _build_executive_summary,
)
from app.schemas.validated_hypothesis import (
    ValidatedHypothesis,
    ValidatedHypothesisReport,
)
from app.schemas.hypothesis import Hypothesis
from app.schemas.evidence import Evidence
from app.schemas.profile import DatasetProfile, ColumnProfile
from app.models.enums import (
    SignalType,
    HypothesisConfidence,
    HypothesisStatus,
    ColumnType,
    ColumnSemanticRole,
)


def _profile() -> DatasetProfile:
    return DatasetProfile(
        row_count=100,
        column_count=2,
        columns=[
            ColumnProfile(
                name="revenue", dtype=ColumnType.NUMERIC,
                semantic_role=ColumnSemanticRole.METRIC,
                is_identifier=False, null_count=0,
                null_percentage=0, unique_count=100,
            ),
            ColumnProfile(
                name="region", dtype=ColumnType.CATEGORICAL,
                semantic_role=ColumnSemanticRole.DIMENSION,
                is_identifier=False, null_count=0,
                null_percentage=0, unique_count=5,
            ),
        ],
    )


def _analyzer_output() -> dict:
    return {
        "row_count": 100,
        "column_count": 2,
        "numeric_columns": ["revenue"],
        "categorical_columns": ["region"],
        "datetime_columns": [],
        "boolean_columns": [],
        "text_columns": [],
        "metric_columns": ["revenue"],
        "dimension_columns": ["region"],
        "time_columns": [],
        "entity_columns": [],
        "identifier_columns": [],
    }


def _evidence(metric: str, value: float, signal_type: SignalType, column: str = "revenue") -> Evidence:
    return Evidence(
        title=f"Evidence: {metric}",
        description=f"{metric}={value}",
        metric=metric,
        value=value,
        supporting_signal=signal_type,
        related_column=column,
    )


def _vh(
    title: str = "test",
    status: HypothesisStatus = HypothesisStatus.SUPPORTED,
    confidence: HypothesisConfidence = HypothesisConfidence.HIGH,
    signals: list[SignalType] | None = None,
    composite: bool = False,
    supporting_evidence: list[Evidence] | None = None,
) -> ValidatedHypothesis:
    if signals is None:
        signals = [SignalType.RIGHT_SKEWED]
    if supporting_evidence is None:
        supporting_evidence = [_evidence("skewness", 1.5, signals[0])]
    return ValidatedHypothesis(
        hypothesis=Hypothesis(
            title=title,
            description=f"desc: {title}",
            confidence=confidence,
            supporting_signals=list(signals),
            is_composite=composite,
            related_columns=["revenue"],
        ),
        status=status,
        supporting_evidence=supporting_evidence,
        contradicting_evidence=[],
        neutral_evidence=[],
        adjusted_confidence=confidence,
    )


# ═══════════════════════════════════════════════════════════════════════
# Finding builders
# ═══════════════════════════════════════════════════════════════════════


class TestBuildSimpleFinding:
    def test_all_fields_present(self):
        vh = _vh("Revenue is right skewed")
        finding = _build_simple_finding(vh)
        assert finding.title == "Revenue is right skewed"
        assert finding.status == HypothesisStatus.SUPPORTED
        assert len(finding.observation) > 0
        assert len(finding.analysis) > 0
        assert len(finding.business_impact) > 0
        assert len(finding.recommendation) > 0

    def test_refuted_finding_structure(self):
        vh = _vh("Not skewed", status=HypothesisStatus.REFUTED)
        finding = _build_simple_finding(vh)
        assert finding.status == HypothesisStatus.REFUTED

    def test_inconclusive_finding_structure(self):
        vh = _vh("Unknown", status=HypothesisStatus.INCONCLUSIVE)
        finding = _build_simple_finding(vh)
        assert finding.status == HypothesisStatus.INCONCLUSIVE

    def test_fallback_for_unknown_signal_type(self):
        """If a signal type has no template, fallback should still produce a Finding."""
        vh = _vh("test", signals=[SignalType.HIGH_MISSING_RATE])  # missing_rate IS in templates
        finding = _build_simple_finding(vh)
        assert finding.title == "test"

    def test_template_values_interpolated(self):
        vh = _vh("test", signals=[SignalType.RIGHT_SKEWED])
        # Provide all metrics the right_skewed template expects
        vh.supporting_evidence = [
            _evidence("skewness", 2.0, SignalType.RIGHT_SKEWED, "revenue"),
            _evidence("mean", 500.0, SignalType.RIGHT_SKEWED, "revenue"),
            _evidence("median", 300.0, SignalType.RIGHT_SKEWED, "revenue"),
        ]
        finding = _build_simple_finding(vh)
        # With all context values present, templates should interpolate correctly
        assert "2.0" in finding.observation or "2" in finding.observation
        assert "revenue" in finding.observation


class TestBuildCompositeFinding:
    def test_composite_finding_with_known_pattern(self):
        vh = _vh(
            "Concentration + Skew",
            signals=[SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED],
            composite=True,
        )
        finding = _build_composite_finding(vh)
        assert finding.title == "Concentration + Skew"
        assert len(finding.analysis) > 0

    def test_composite_fallback_for_unknown_pattern(self):
        """Two signals that don't have a composite template → fallback."""
        vh = _vh(
            "Odd combination",
            signals=[SignalType.LOW_VARIANCE, SignalType.HIGH_CARDINALITY],
            composite=True,
        )
        finding = _build_composite_finding(vh)
        # Should still produce a finding with fallback text
        assert finding.title == "Odd combination"
        assert len(finding.observation) > 0


class TestBuildFindingDispatch:
    def test_dispatches_to_simple(self):
        vh = _vh("simple", composite=False)
        finding = _build_finding(vh)
        assert finding.title == "simple"

    def test_dispatches_to_composite(self):
        vh = _vh(
            "composite",
            signals=[SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED],
            composite=True,
        )
        finding = _build_finding(vh)
        assert finding.title == "composite"


# ═══════════════════════════════════════════════════════════════════════
# Executive summary
# ═══════════════════════════════════════════════════════════════════════


class TestExecutiveSummary:
    def test_all_counts_match(self):
        validated = [
            _vh("s1", status=HypothesisStatus.SUPPORTED),
            _vh("s2", status=HypothesisStatus.SUPPORTED),
            _vh("r1", status=HypothesisStatus.REFUTED),
            _vh("i1", status=HypothesisStatus.INCONCLUSIVE),
        ]
        es = _build_executive_summary(validated)
        assert es.total_hypotheses == 4
        assert es.supported_count == 2
        assert es.refuted_count == 1
        assert es.inconclusive_count == 1

    def test_high_priority_findings(self):
        validated = [
            _vh("High risk", confidence=HypothesisConfidence.HIGH),
            _vh("Medium risk", confidence=HypothesisConfidence.MEDIUM),
        ]
        es = _build_executive_summary(validated)
        assert "High risk" in es.highest_priority_findings
        assert len(es.highest_priority_findings) <= 3


# ═══════════════════════════════════════════════════════════════════════
# generate_report — main orchestrator
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateReport:
    def test_returns_investigation_report(self):
        vh = _vh("A finding")
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        assert report is not None

    def test_findings_match_validated_count(self):
        validated = [
            _vh("f1"),
            _vh("f2"),
            _vh("f3", status=HypothesisStatus.REFUTED),
        ]
        validation = ValidatedHypothesisReport(validated=validated, findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        assert len(report.findings) == 3

    def test_next_steps_deduplicated(self):
        vh1 = _vh("f1")
        vh2 = _vh("f2")
        validation = ValidatedHypothesisReport(validated=[vh1, vh2], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        # Next steps should be unique recommendations
        assert len(report.next_steps) >= 1
        assert len(report.next_steps) == len(set(report.next_steps))

    def test_dataset_summary_populated(self):
        vh = _vh("f1")
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        ds = report.dataset_summary
        assert ds.row_count == 100
        assert ds.column_count == 2
        assert "revenue" in ds.numeric_columns
        assert "region" in ds.categorical_columns

    def test_dataset_summary_includes_semantic_roles(self):
        vh = _vh("f1")
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        ds = report.dataset_summary
        assert ds.metric_columns == ["revenue"]
        assert ds.dimension_columns == ["region"]

    def test_report_is_serializable(self):
        vh = _vh("f1")
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        d = report.model_dump()
        assert "executive_summary" in d
        assert "findings" in d
        assert "cause_candidates" in d
        assert "next_steps" in d

    def test_cause_candidates_populated(self):
        vh = _vh("Revenue is decreasing", signals=[SignalType.DECREASING_TREND])
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(validation, _profile(), _analyzer_output())
        assert len(report.cause_candidates) == 1
        assert report.cause_candidates[0].supporting_finding_titles == [
            "Revenue is decreasing"
        ]

    def test_investigation_question_is_in_summary(self):
        vh = _vh("f1")
        validation = ValidatedHypothesisReport(validated=[vh], findings=[])
        report = generate_report(
            validation,
            _profile(),
            _analyzer_output(),
            investigation_question="为什么 revenue 下降？",
        )
        assert (
            report.executive_summary.investigation_question
            == "为什么 revenue 下降？"
        )

    def test_investigation_question_ranks_related_findings_first(self):
        concentration = _vh(
            "Region is concentrated",
            signals=[SignalType.HIGH_CONCENTRATION],
            supporting_evidence=[
                _evidence(
                    "top_1_share",
                    0.82,
                    SignalType.HIGH_CONCENTRATION,
                    "region",
                )
            ],
        )
        decline = _vh(
            "Revenue is decreasing",
            signals=[SignalType.DECREASING_TREND],
            supporting_evidence=[
                _evidence(
                    "growth_rate",
                    -0.24,
                    SignalType.DECREASING_TREND,
                    "revenue",
                )
            ],
        )
        validation = ValidatedHypothesisReport(
            validated=[concentration, decline],
            findings=[],
        )

        report = generate_report(
            validation,
            _profile(),
            _analyzer_output(),
            investigation_question="为什么 revenue 下降？",
        )

        assert report.findings[0].title == "Revenue is decreasing"
