"""Tests for app/services/evidence/ — parametrized across all 7 builders."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from app.services.evidence import generate_all_evidence, generate_evidence_for_hypothesis
from app.services.evidence.distribution import build_distribution_evidence
from app.services.evidence.outlier import build_outlier_evidence
from app.services.evidence.trend import build_trend_evidence
from app.services.evidence.concentration import build_concentration_evidence
from app.services.evidence.missing_rate import build_missing_rate_evidence
from app.services.evidence.cardinality import build_cardinality_evidence
from app.services.evidence.variance import build_variance_evidence

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal, SignalReport
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.models.enums import SignalType, SignalSeverity, HypothesisConfidence


def _profile(df: pd.DataFrame) -> DatasetProfile:
    from app.services.profiler import profile_dataframe
    return profile_dataframe(df)


def _signal(signal_type: SignalType, column: str) -> Signal:
    return Signal(
        type=signal_type,
        severity=SignalSeverity.WARNING,
        column=column,
        message=f"Test signal: {signal_type.value} in {column}",
    )


# ═══════════════════════════════════════════════════════════════════════
# Distribution evidence
# ═══════════════════════════════════════════════════════════════════════


class TestDistributionEvidence:
    def test_produces_four_metrics(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        evidence = build_distribution_evidence(right_skewed_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert {"mean", "median", "std", "skewness"}.issubset(metrics)
        assert "count" in metrics

    def test_values_are_numeric(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        evidence = build_distribution_evidence(right_skewed_df, profile, signal)
        for e in evidence:
            assert e.value is not None
            float(e.value)  # should not raise

    def test_skewness_positive_for_right_skew(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        evidence = build_distribution_evidence(right_skewed_df, profile, signal)
        skew = next(e for e in evidence if e.metric == "skewness")
        assert float(skew.value) > 0

    def test_signal_type_preserved(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        evidence = build_distribution_evidence(right_skewed_df, profile, signal)
        for e in evidence:
            assert e.supporting_signal == SignalType.RIGHT_SKEWED

    def test_too_few_values_returns_empty(self):
        df = pd.DataFrame({"value": [1.0]})
        profile = _profile(df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        evidence = build_distribution_evidence(df, profile, signal)
        assert len(evidence) == 0


# ═══════════════════════════════════════════════════════════════════════
# Outlier evidence
# ═══════════════════════════════════════════════════════════════════════


class TestOutlierEvidence:
    def test_produces_metrics(self, outlier_df):
        profile = _profile(outlier_df)
        signal = _signal(SignalType.OUTLIER_DETECTED, "revenue")
        evidence = build_outlier_evidence(outlier_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert "outlier_count" in metrics

    def test_outlier_count_positive(self, outlier_df):
        profile = _profile(outlier_df)
        signal = _signal(SignalType.OUTLIER_DETECTED, "revenue")
        evidence = build_outlier_evidence(outlier_df, profile, signal)
        count = next(e for e in evidence if e.metric == "outlier_count")
        assert float(count.value) > 0


# ═══════════════════════════════════════════════════════════════════════
# Trend evidence
# ═══════════════════════════════════════════════════════════════════════


class TestTrendEvidence:
    def test_increasing_trend_growth_positive(self, increasing_trend_df):
        profile = _profile(increasing_trend_df)
        signal = _signal(SignalType.INCREASING_TREND, "sales")
        evidence = build_trend_evidence(increasing_trend_df, profile, signal)
        growth = next(e for e in evidence if e.metric == "growth_rate")
        assert float(growth.value) > 0

    def test_decreasing_trend_growth_negative(self, decreasing_trend_df):
        profile = _profile(decreasing_trend_df)
        signal = _signal(SignalType.DECREASING_TREND, "sales")
        evidence = build_trend_evidence(decreasing_trend_df, profile, signal)
        growth = next(e for e in evidence if e.metric == "growth_rate")
        assert float(growth.value) < 0

    def test_produces_all_metrics(self, increasing_trend_df):
        profile = _profile(increasing_trend_df)
        signal = _signal(SignalType.INCREASING_TREND, "sales")
        evidence = build_trend_evidence(increasing_trend_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert {"first_val", "last_val", "absolute_change", "growth_rate"}.issubset(metrics)
        assert "trend_points" in metrics
        assert "r_squared" in metrics


# ═══════════════════════════════════════════════════════════════════════
# Concentration evidence
# ═══════════════════════════════════════════════════════════════════════


class TestConcentrationEvidence:
    def test_produces_share_metrics(self, concentration_df):
        profile = _profile(concentration_df)
        signal = _signal(SignalType.HIGH_CONCENTRATION, "category")
        evidence = build_concentration_evidence(concentration_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert "top_1_share" in metrics

    def test_top_1_share_is_high(self, concentration_df):
        profile = _profile(concentration_df)
        signal = _signal(SignalType.HIGH_CONCENTRATION, "category")
        evidence = build_concentration_evidence(concentration_df, profile, signal)
        top1 = next(e for e in evidence if e.metric == "top_1_share")
        assert float(top1.value) > 0.5


# ═══════════════════════════════════════════════════════════════════════
# Missing rate evidence
# ═══════════════════════════════════════════════════════════════════════


class TestMissingRateEvidence:
    def test_produces_metrics(self, missing_rate_df):
        profile = _profile(missing_rate_df)
        signal = _signal(SignalType.HIGH_MISSING_RATE, "col_a")
        evidence = build_missing_rate_evidence(missing_rate_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert "null_percentage" in metrics
        # build_missing_rate_evidence produces one evidence item per call
        assert len(evidence) == 1

    def test_null_percentage_correct(self, missing_rate_df):
        profile = _profile(missing_rate_df)
        signal = _signal(SignalType.HIGH_MISSING_RATE, "col_a")
        evidence = build_missing_rate_evidence(missing_rate_df, profile, signal)
        pct = next(e for e in evidence if e.metric == "null_percentage")
        # 3 nulls out of 8 = 37.5%
        assert float(pct.value) == pytest.approx(37.5, abs=1.0)


# ═══════════════════════════════════════════════════════════════════════
# Cardinality evidence
# ═══════════════════════════════════════════════════════════════════════


class TestCardinalityEvidence:
    def test_produces_metrics(self, high_cardinality_df):
        profile = _profile(high_cardinality_df)
        signal = _signal(SignalType.HIGH_CARDINALITY, "col_a")
        evidence = build_cardinality_evidence(high_cardinality_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert "unique_count" in metrics
        assert "unique_ratio" in metrics

    def test_unique_ratio_is_high(self, high_cardinality_df):
        profile = _profile(high_cardinality_df)
        signal = _signal(SignalType.HIGH_CARDINALITY, "col_a")
        evidence = build_cardinality_evidence(high_cardinality_df, profile, signal)
        ratio = next(e for e in evidence if e.metric == "unique_ratio")
        assert float(ratio.value) > 0.9


# ═══════════════════════════════════════════════════════════════════════
# Variance evidence
# ═══════════════════════════════════════════════════════════════════════


class TestVarianceEvidence:
    def test_produces_cv_metric(self, low_variance_df):
        profile = _profile(low_variance_df)
        signal = _signal(SignalType.LOW_VARIANCE, "price")
        evidence = build_variance_evidence(low_variance_df, profile, signal)
        metrics = {e.metric for e in evidence}
        assert "coefficient_of_variation" in metrics

    def test_cv_is_low(self, low_variance_df):
        profile = _profile(low_variance_df)
        signal = _signal(SignalType.LOW_VARIANCE, "price")
        evidence = build_variance_evidence(low_variance_df, profile, signal)
        cv = next(e for e in evidence if e.metric == "coefficient_of_variation")
        assert float(cv.value) < 0.05


# ═══════════════════════════════════════════════════════════════════════
# generate_evidence_for_hypothesis — integration
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateEvidenceForHypothesis:
    def test_returns_evidence_for_simple_hypothesis(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        signal_report = SignalReport(signals=[signal])
        hypothesis = Hypothesis(
            title="test",
            description="test",
            confidence=HypothesisConfidence.MEDIUM,
            supporting_signals=[SignalType.RIGHT_SKEWED],
            related_columns=["value"],
        )
        evidence = generate_evidence_for_hypothesis(
            right_skewed_df, profile, hypothesis, signal_report
        )
        metrics = {e.metric for e in evidence}
        assert {"mean", "median", "std", "skewness"}.issubset(metrics)

    def test_no_matching_signal_returns_empty(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal_report = SignalReport(signals=[])  # no signals
        hypothesis = Hypothesis(
            title="test",
            description="test",
            confidence=HypothesisConfidence.MEDIUM,
            supporting_signals=[SignalType.RIGHT_SKEWED],
            related_columns=["value"],
        )
        evidence = generate_evidence_for_hypothesis(
            right_skewed_df, profile, hypothesis, signal_report
        )
        assert len(evidence) == 0


# ═══════════════════════════════════════════════════════════════════════
# generate_all_evidence — integration
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateAllEvidence:
    def test_returns_parallel_lists(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signal = _signal(SignalType.RIGHT_SKEWED, "value")
        signal_report = SignalReport(signals=[signal])
        hypothesis = Hypothesis(
            title="test",
            description="test",
            confidence=HypothesisConfidence.MEDIUM,
            supporting_signals=[SignalType.RIGHT_SKEWED],
            related_columns=["value"],
        )
        hypothesis_report = HypothesisReport(hypotheses=[hypothesis])
        result = generate_all_evidence(
            right_skewed_df, profile, hypothesis_report, signal_report
        )
        assert len(result) == 1
        metrics = {e.metric for e in result[0]}
        assert {"mean", "median", "std", "skewness"}.issubset(metrics)
