"""Tests for app/services/cross_dataset_analyzer.py — Phase 9."""

import pytest
from app.services.cross_dataset_analyzer import CrossDatasetAnalyzer
from app.schemas.cross_dataset import InvestigationGraph, CrossDatasetRelation
from app.schemas.investigation_report import (
    InvestigationReport,
    ExecutiveSummary,
    DatasetSummary,
    Finding,
)
from app.schemas.profile import DatasetProfile, ColumnProfile
from app.schemas.signal import SignalReport, Signal
from app.schemas.evidence import Evidence
from app.models.enums import (
    SignalType,
    SignalSeverity,
    HypothesisStatus,
    HypothesisConfidence,
    ColumnType,
    ColumnSemanticRole,
)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _role_for(dtype: ColumnType, is_identifier: bool) -> ColumnSemanticRole:
    if is_identifier:
        return ColumnSemanticRole.IDENTIFIER
    if dtype == ColumnType.NUMERIC:
        return ColumnSemanticRole.METRIC
    if dtype == ColumnType.DATETIME:
        return ColumnSemanticRole.TIME
    return ColumnSemanticRole.DIMENSION


def _column(
    name: str,
    dtype: ColumnType,
    is_identifier: bool,
    unique_count: int = 50,
) -> ColumnProfile:
    return ColumnProfile(
        name=name,
        dtype=dtype,
        semantic_role=_role_for(dtype, is_identifier),
        is_identifier=is_identifier,
        null_count=0,
        null_percentage=0,
        unique_count=unique_count,
    )


def _profile(columns: list[tuple[str, ColumnType, bool]]) -> DatasetProfile:
    """Build a DatasetProfile from (name, dtype, is_identifier) tuples."""
    return DatasetProfile(
        row_count=100, column_count=len(columns),
        columns=[
            _column(name, dtype, is_id)
            for name, dtype, is_id in columns
        ],
    )


def _signal_report(types: list[SignalType]) -> SignalReport:
    """Build a SignalReport with given signal types."""
    return SignalReport(signals=[
        Signal(type=t, severity=SignalSeverity.INFO, column="test", message="test")
        for t in types
    ])


def _finding_with_signal(
    title: str, signal_type: SignalType, status=HypothesisStatus.SUPPORTED,
) -> Finding:
    """Build a Finding with a specific signal type in its evidence."""
    return Finding(
        title=title, observation="obs", status=status,
        confidence=HypothesisConfidence.MEDIUM,
        supporting_evidence=[
            Evidence(
                title="test", description="test", metric="m",
                value=1, supporting_signal=signal_type, related_column="test",
            )
        ],
        contradicting_evidence=[],
        analysis="analysis", business_impact="impact", recommendation="rec",
    )


def _report(findings: list[Finding]) -> InvestigationReport:
    supported = sum(1 for f in findings if f.status == HypothesisStatus.SUPPORTED)
    return InvestigationReport(
        executive_summary=ExecutiveSummary(
            total_hypotheses=len(findings), supported_count=supported,
            refuted_count=0, inconclusive_count=0,
            highest_priority_findings=[], overall_risk="low", overall_confidence="high",
        ),
        dataset_summary=DatasetSummary(
            row_count=100, column_count=3,
            numeric_columns=["revenue"], categorical_columns=["region"],
            datetime_columns=["date"], text_columns=[], boolean_columns=[],
        ),
        findings=findings, next_steps=[],
    )


def _analyzer() -> CrossDatasetAnalyzer:
    return CrossDatasetAnalyzer()


# ═══════════════════════════════════════════════════════════════════════
# Detection rule tests
# ═══════════════════════════════════════════════════════════════════════


class TestSharedDimensions:
    def test_detects_shared_column(self):
        primary_cols = {
            "revenue": _column("revenue", ColumnType.NUMERIC, False, 100),
            "region": _column("region", ColumnType.CATEGORICAL, False, 5),
        }
        sec_cols = {
            "region": _column("region", ColumnType.CATEGORICAL, False, 5),
            "churn_rate": _column("churn_rate", ColumnType.NUMERIC, False),
        }
        result = _analyzer()._find_shared_dimensions(primary_cols, sec_cols)
        assert result == {"region"}

    def test_identifiers_excluded(self):
        primary_cols = {
            "customer_id": _column("customer_id", ColumnType.TEXT, True, 100),
        }
        sec_cols = {
            "customer_id": _column("customer_id", ColumnType.TEXT, True, 100),
        }
        result = _analyzer()._find_shared_dimensions(primary_cols, sec_cols)
        assert result == set()

    def test_no_shared_columns(self):
        primary_cols = {"a": _column("a", ColumnType.NUMERIC, False, 100)}
        sec_cols = {"b": _column("b", ColumnType.NUMERIC, False, 100)}
        result = _analyzer()._find_shared_dimensions(primary_cols, sec_cols)
        assert result == set()


class TestTrendCorrelation:
    def test_correlated_both_increasing(self):
        relations = _analyzer()._detect_trend_correlation(
            {SignalType.INCREASING_TREND},
            {SignalType.INCREASING_TREND},
            set(), "sec.csv",
        )
        assert any(r.type == "correlated_trend" for r in relations)

    def test_correlated_both_decreasing(self):
        relations = _analyzer()._detect_trend_correlation(
            {SignalType.DECREASING_TREND},
            {SignalType.DECREASING_TREND},
            set(), "sec.csv",
        )
        assert any(r.type == "correlated_trend" for r in relations)

    def test_opposite_trends(self):
        relations = _analyzer()._detect_trend_correlation(
            {SignalType.INCREASING_TREND},
            {SignalType.DECREASING_TREND},
            set(), "sec.csv",
        )
        assert any(r.type == "opposite_trend" for r in relations)

    def test_no_trends_no_relations(self):
        relations = _analyzer()._detect_trend_correlation(
            {SignalType.OUTLIER_DETECTED},
            {SignalType.RIGHT_SKEWED},
            set(), "sec.csv",
        )
        assert len(relations) == 0

    def test_shared_dims_increase_confidence(self):
        relations = _analyzer()._detect_trend_correlation(
            {SignalType.DECREASING_TREND},
            {SignalType.DECREASING_TREND},
            {"region"}, "sec.csv",
        )
        correlated = [r for r in relations if r.type == "correlated_trend"]
        assert len(correlated) > 0
        assert "region" in correlated[0].description


class TestComplementarySignals:
    def test_concentration_plus_trend(self):
        relations = _analyzer()._detect_complementary_signals(
            {SignalType.HIGH_CONCENTRATION},
            {SignalType.DECREASING_TREND},
            set(), "sec.csv",
        )
        assert any(r.type == "complementary_signal" for r in relations)

    def test_shared_dims_boost_confidence(self):
        relations = _analyzer()._detect_complementary_signals(
            {SignalType.HIGH_CONCENTRATION},
            {SignalType.DECREASING_TREND},
            {"region"}, "sec.csv",
        )
        comp = [r for r in relations if r.type == "complementary_signal"]
        assert len(comp) > 0
        assert comp[0].confidence == "high"

    def test_no_concentration_no_signal(self):
        relations = _analyzer()._detect_complementary_signals(
            {SignalType.OUTLIER_DETECTED},
            {SignalType.INCREASING_TREND},
            set(), "sec.csv",
        )
        assert len(relations) == 0


# ═══════════════════════════════════════════════════════════════════════
# Full graph construction
# ═══════════════════════════════════════════════════════════════════════


class TestAnalyze:
    def test_returns_investigation_graph(self):
        primary_profile = _profile([
            ("revenue", ColumnType.NUMERIC, False),
            ("region", ColumnType.CATEGORICAL, False),
        ])
        primary_findings = [
            _finding_with_signal("Revenue decline", SignalType.DECREASING_TREND),
            _finding_with_signal("Concentration risk", SignalType.HIGH_CONCENTRATION),
        ]
        primary_report = _report(primary_findings)

        sec_profile = _profile([
            ("region", ColumnType.CATEGORICAL, False),
            ("churn_rate", ColumnType.NUMERIC, False),
        ])
        sec_signals = _signal_report([SignalType.DECREASING_TREND])

        graph = _analyzer().analyze(
            primary_report, primary_profile,
            [sec_profile], [sec_signals], ["churn.csv"],
        )

        assert isinstance(graph, InvestigationGraph)
        assert graph.primary_dataset == "primary"
        assert "churn.csv" in graph.secondary_datasets
        assert "region" in graph.shared_dimensions
        # Should have at least: shared_dimension, correlated_trend,
        # complementary_signal = 3 relations
        assert len(graph.relations) >= 3
        assert len(graph.cross_hypotheses) >= 3

    def test_no_shared_dims_no_secondary_signals(self):
        """Datasets with nothing in common and no signals — minimal graph."""
        primary_profile = _profile([("revenue", ColumnType.NUMERIC, False)])
        primary_report = _report([])

        sec_profile = _profile([("churn", ColumnType.NUMERIC, False)])
        sec_signals = _signal_report([])

        graph = _analyzer().analyze(
            primary_report, primary_profile,
            [sec_profile], [sec_signals], ["empty.csv"],
        )

        assert len(graph.shared_dimensions) == 0
        assert len(graph.relations) == 0
        assert len(graph.cross_hypotheses) == 0

    def test_multiple_secondaries(self):
        primary_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        primary_findings = [
            _finding_with_signal("Revenue down", SignalType.DECREASING_TREND),
        ]
        primary_report = _report(primary_findings)

        sec1_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        sec1_signals = _signal_report([SignalType.DECREASING_TREND])

        sec2_profile = _profile([("date", ColumnType.DATETIME, False)])
        sec2_signals = _signal_report([SignalType.INCREASING_TREND])

        graph = _analyzer().analyze(
            primary_report, primary_profile,
            [sec1_profile, sec2_profile],
            [sec1_signals, sec2_signals],
            ["churn.csv", "ops.csv"],
        )

        assert len(graph.secondary_datasets) == 2
        assert "region" in graph.shared_dimensions
        # At least shared_dim + correlated for sec1 + opposite for sec2
        assert len(graph.relations) >= 3

    def test_deterministic_output(self):
        primary_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        primary_findings = [
            _finding_with_signal("Revenue down", SignalType.DECREASING_TREND),
        ]
        primary_report = _report(primary_findings)
        sec_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        sec_signals = _signal_report([SignalType.DECREASING_TREND])

        g1 = _analyzer().analyze(
            primary_report, primary_profile,
            [sec_profile], [sec_signals], ["churn.csv"],
        )
        g2 = _analyzer().analyze(
            primary_report, primary_profile,
            [sec_profile], [sec_signals], ["churn.csv"],
        )

        assert g1.shared_dimensions == g2.shared_dimensions
        assert len(g1.relations) == len(g2.relations)
        assert g1.cross_hypotheses == g2.cross_hypotheses

    def test_graph_is_serializable(self):
        primary_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        primary_report = _report([
            _finding_with_signal("Revenue down", SignalType.DECREASING_TREND),
        ])
        sec_profile = _profile([("region", ColumnType.CATEGORICAL, False)])
        sec_signals = _signal_report([SignalType.DECREASING_TREND])

        graph = _analyzer().analyze(
            primary_report, primary_profile,
            [sec_profile], [sec_signals], ["churn.csv"],
        )
        d = graph.model_dump()
        assert "primary_dataset" in d
        assert "secondary_datasets" in d
        assert "shared_dimensions" in d
        assert "relations" in d
        assert "cross_hypotheses" in d
