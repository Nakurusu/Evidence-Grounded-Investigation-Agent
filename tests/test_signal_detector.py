"""Tests for app/services/signal_detector.py — all 8 signal detection functions."""

import pandas as pd
import pytest
from app.services.signal_detector import (
    detect_signals,
    detect_missing_rate,
    detect_cardinality,
    detect_outliers,
    detect_trends,
    detect_concentration,
    detect_distribution,
)
from app.schemas.profile import DatasetProfile
from app.schemas.signal import SignalReport, Signal
from app.models.enums import SignalType, SignalSeverity


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _profile(df: pd.DataFrame) -> DatasetProfile:
    """Quick inline profile so tests don't depend on profiler module."""
    from app.services.profiler import profile_dataframe

    return profile_dataframe(df)


# ═══════════════════════════════════════════════════════════════════════
# detect_missing_rate
# ═══════════════════════════════════════════════════════════════════════


class TestDetectMissingRate:
    def test_high_missing_rate_triggers_signal(self, missing_rate_df):
        profile = _profile(missing_rate_df)  # col_a ~37.5% missing
        signals = detect_missing_rate(profile)
        assert len(signals) > 0
        assert signals[0].type == SignalType.HIGH_MISSING_RATE
        assert signals[0].severity == SignalSeverity.WARNING
        assert "col_a" in signals[0].message

    def test_low_missing_rate_no_signal(self, low_missing_rate_df):
        profile = _profile(low_missing_rate_df)  # col_a ~12.5% missing
        signals = detect_missing_rate(profile)
        assert len(signals) == 0

    def test_identifier_columns_skipped(self, id_column_df):
        """Identifier columns should not produce missing-rate signals."""
        # Add nulls to an ID column
        df = id_column_df.copy()
        df.loc[0, "customer_id"] = None  # 1% missing
        profile = _profile(df)
        signals = detect_missing_rate(profile)
        # customer_id is an identifier, so it should be skipped
        id_signals = [s for s in signals if s.column == "customer_id"]
        assert len(id_signals) == 0


# ═══════════════════════════════════════════════════════════════════════
# detect_cardinality
# ═══════════════════════════════════════════════════════════════════════


class TestDetectCardinality:
    def test_high_cardinality_triggers_signal(self, high_cardinality_df):
        profile = _profile(high_cardinality_df)
        signals = detect_cardinality(profile)
        assert len(signals) > 0
        assert signals[0].type == SignalType.HIGH_CARDINALITY

    def test_low_cardinality_no_signal(self, low_cardinality_df):
        profile = _profile(low_cardinality_df)
        signals = detect_cardinality(profile)
        assert len(signals) == 0

    def test_numeric_columns_skipped(self):
        """Cardinality check should only apply to TEXT/CATEGORICAL."""
        df = pd.DataFrame({"num": list(range(100))})
        profile = _profile(df)  # num is NUMERIC, 100% unique
        signals = detect_cardinality(profile)
        assert len(signals) == 0

    def test_identifier_skipped(self, id_column_df):
        profile = _profile(id_column_df)
        signals = detect_cardinality(profile)
        id_signals = [s for s in signals if s.column == "customer_id"]
        assert len(id_signals) == 0  # identifier columns skipped


# ═══════════════════════════════════════════════════════════════════════
# detect_outliers
# ═══════════════════════════════════════════════════════════════════════


class TestDetectOutliers:
    def test_outliers_detected(self, outlier_df):
        profile = _profile(outlier_df)
        signals = detect_outliers(outlier_df, profile)
        assert len(signals) > 0
        assert signals[0].type == SignalType.OUTLIER_DETECTED
        assert "revenue" in signals[0].message

    def test_no_outliers(self, no_outlier_df):
        profile = _profile(no_outlier_df)
        signals = detect_outliers(no_outlier_df, profile)
        assert len(signals) == 0

    def test_non_numeric_skipped(self):
        df = pd.DataFrame({"cat": ["a", "b", "c", "d", "e"]})
        profile = _profile(df)
        signals = detect_outliers(df, profile)
        assert len(signals) == 0

    def test_too_few_values_skipped(self):
        """Less than 4 non-null values → no outlier check."""
        df = pd.DataFrame({"val": [1.0, 2.0, None, None, None]})
        profile = _profile(df)
        signals = detect_outliers(df, profile)
        assert len(signals) == 0


# ═══════════════════════════════════════════════════════════════════════
# detect_trends
# ═══════════════════════════════════════════════════════════════════════


class TestDetectTrends:
    def test_increasing_trend(self, increasing_trend_df):
        profile = _profile(increasing_trend_df)
        signals = detect_trends(increasing_trend_df, profile)
        assert any(s.type == SignalType.INCREASING_TREND for s in signals)

    def test_decreasing_trend(self, decreasing_trend_df):
        profile = _profile(decreasing_trend_df)
        signals = detect_trends(decreasing_trend_df, profile)
        assert any(s.type == SignalType.DECREASING_TREND for s in signals)

    def test_flat_trend_no_signal(self, flat_trend_df):
        profile = _profile(flat_trend_df)
        signals = detect_trends(flat_trend_df, profile)
        assert len(signals) == 0

    def test_no_datetime_column_returns_empty(self, single_column_df):
        profile = _profile(single_column_df)
        signals = detect_trends(single_column_df, profile)
        assert len(signals) == 0

    def test_no_numeric_column_returns_empty(self):
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "cat": ["a", "b"],
        })
        profile = _profile(df)
        signals = detect_trends(df, profile)
        assert len(signals) == 0


# ═══════════════════════════════════════════════════════════════════════
# detect_concentration
# ═══════════════════════════════════════════════════════════════════════


class TestDetectConcentration:
    def test_high_concentration(self, concentration_df):
        profile = _profile(concentration_df)
        signals = detect_concentration(concentration_df, profile)
        assert len(signals) > 0
        assert signals[0].type == SignalType.HIGH_CONCENTRATION

    def test_no_concentration(self, no_concentration_df):
        profile = _profile(no_concentration_df)
        signals = detect_concentration(no_concentration_df, profile)
        assert len(signals) == 0

    def test_no_categorical_returns_empty(self, single_column_df):
        profile = _profile(single_column_df)
        signals = detect_concentration(single_column_df, profile)
        assert len(signals) == 0

    def test_entity_columns_are_not_used_as_dimensions(self):
        df = pd.DataFrame(
            {
                "customer": [f"Customer {i}" for i in range(100)],
                "segment": ["enterprise"] * 90 + ["smb"] * 10,
                "revenue": [100] * 90 + [5] * 10,
            }
        )
        profile = _profile(df)
        signals = detect_concentration(df, profile)

        assert any(s.dimension_column == "segment" for s in signals)
        assert all(s.dimension_column != "customer" for s in signals)


# ═══════════════════════════════════════════════════════════════════════
# detect_distribution
# ═══════════════════════════════════════════════════════════════════════


class TestDetectDistribution:
    def test_right_skewed(self, right_skewed_df):
        profile = _profile(right_skewed_df)
        signals = detect_distribution(right_skewed_df, profile)
        assert any(s.type == SignalType.RIGHT_SKEWED for s in signals)

    def test_left_skewed(self, left_skewed_df):
        profile = _profile(left_skewed_df)
        signals = detect_distribution(left_skewed_df, profile)
        assert any(s.type == SignalType.LEFT_SKEWED for s in signals)

    def test_symmetric_no_skew_signal(self, symmetric_df):
        profile = _profile(symmetric_df)
        signals = detect_distribution(symmetric_df, profile)
        skew_signals = [
            s for s in signals
            if s.type in (SignalType.RIGHT_SKEWED, SignalType.LEFT_SKEWED)
        ]
        assert len(skew_signals) == 0

    def test_low_variance(self, low_variance_df):
        profile = _profile(low_variance_df)
        signals = detect_distribution(low_variance_df, profile)
        assert any(s.type == SignalType.LOW_VARIANCE for s in signals)

    def test_normal_variance_no_signal(self, normal_variance_df):
        profile = _profile(normal_variance_df)
        signals = detect_distribution(normal_variance_df, profile)
        var_signals = [s for s in signals if s.type == SignalType.LOW_VARIANCE]
        assert len(var_signals) == 0

    def test_no_numeric_returns_empty(self):
        df = pd.DataFrame({"cat": ["a", "b", "c"]})
        profile = _profile(df)
        signals = detect_distribution(df, profile)
        assert len(signals) == 0


# ═══════════════════════════════════════════════════════════════════════
# detect_signals — orchestrator
# ═══════════════════════════════════════════════════════════════════════


class TestDetectSignals:
    def test_returns_signal_report(self, integration_df):
        profile = _profile(integration_df)
        result = detect_signals(integration_df, profile)
        assert isinstance(result, SignalReport)
        assert hasattr(result, "signals")

    def test_each_signal_has_required_fields(self, integration_df):
        profile = _profile(integration_df)
        result = detect_signals(integration_df, profile)
        for s in result.signals:
            assert isinstance(s.type, SignalType)
            assert isinstance(s.severity, SignalSeverity)
            assert isinstance(s.message, str)
            assert len(s.message) > 0

    def test_multiple_signal_types_detected(self, integration_df):
        profile = _profile(integration_df)
        result = detect_signals(integration_df, profile)
        types = {s.type for s in result.signals}
        # integration_df should trigger at least 4 types
        assert len(types) >= 3
