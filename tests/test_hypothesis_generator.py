"""Tests for app/services/hypothesis_generator.py."""

from app.services.hypothesis_generator import (
    generate_hypotheses,
    generate_composite_hypotheses,
)
from app.schemas.signal import SignalReport, Signal
from app.models.enums import SignalType, SignalSeverity, HypothesisConfidence


def _signal(st: SignalType, sev: SignalSeverity = SignalSeverity.WARNING, col: str = "test_col") -> Signal:
    return Signal(type=st, severity=sev, column=col, message="test")


class TestGenerateHypotheses:
    def test_each_signal_produces_hypothesis(self):
        report = SignalReport(signals=[
            _signal(SignalType.OUTLIER_DETECTED),
            _signal(SignalType.HIGH_CONCENTRATION),
        ])
        result = generate_hypotheses(report)
        simple = [h for h in result.hypotheses if not h.is_composite]
        assert len(simple) == 2

    def test_simple_hypothesis_has_signals(self):
        report = SignalReport(signals=[_signal(SignalType.OUTLIER_DETECTED)])
        result = generate_hypotheses(report)
        h = result.hypotheses[0]
        assert h.is_composite is False
        assert SignalType.OUTLIER_DETECTED in h.supporting_signals

    def test_column_interpolated_in_title(self):
        report = SignalReport(signals=[_signal(SignalType.HIGH_MISSING_RATE, col="revenue")])
        result = generate_hypotheses(report)
        # The title template includes {column}
        assert "revenue" in result.hypotheses[0].title

    def test_high_severity_confidence(self):
        report = SignalReport(signals=[_signal(SignalType.OUTLIER_DETECTED, sev=SignalSeverity.HIGH)])
        result = generate_hypotheses(report)
        assert result.hypotheses[0].confidence == HypothesisConfidence.HIGH

    def test_info_severity_confidence_low(self):
        report = SignalReport(signals=[_signal(SignalType.INCREASING_TREND, sev=SignalSeverity.INFO)])
        result = generate_hypotheses(report)
        assert result.hypotheses[0].confidence == HypothesisConfidence.LOW


class TestCompositeHypotheses:
    def test_composite_generated_when_both_signals_present(self):
        report = SignalReport(signals=[
            _signal(SignalType.HIGH_CONCENTRATION),
            _signal(SignalType.RIGHT_SKEWED),
        ])
        result = generate_composite_hypotheses(report)
        assert len(result) >= 1
        assert result[0].is_composite is True

    def test_no_composite_when_insufficient_signals(self):
        report = SignalReport(signals=[_signal(SignalType.OUTLIER_DETECTED)])
        result = generate_composite_hypotheses(report)
        assert len(result) == 0

    def test_composite_has_both_signal_types(self):
        report = SignalReport(signals=[
            _signal(SignalType.HIGH_CONCENTRATION),
            _signal(SignalType.RIGHT_SKEWED),
        ])
        result = generate_composite_hypotheses(report)
        signals = result[0].supporting_signals
        assert SignalType.HIGH_CONCENTRATION in signals
        assert SignalType.RIGHT_SKEWED in signals

    def test_empty_signal_report(self):
        report = SignalReport(signals=[])
        result = generate_composite_hypotheses(report)
        assert len(result) == 0
