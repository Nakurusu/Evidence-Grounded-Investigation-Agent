"""Tests for app/services/hypothesis_validator.py."""

import pytest
from app.services.hypothesis_validator import (
    validate_hypotheses,
    _classify_evidence,
    _determine_status,
)
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.schemas.evidence import Evidence
from app.models.enums import SignalType, HypothesisConfidence, HypothesisStatus


def _hypothesis(
    title: str = "test",
    signals: list[SignalType] | None = None,
    confidence: HypothesisConfidence = HypothesisConfidence.MEDIUM,
    composite: bool = False,
    columns: list[str] | None = None,
) -> Hypothesis:
    if signals is None:
        signals = [SignalType.RIGHT_SKEWED]
    if columns is None:
        columns = ["value"]
    return Hypothesis(
        title=title,
        description=f"desc: {title}",
        confidence=confidence,
        supporting_signals=list(signals),
        is_composite=composite,
        related_columns=columns,
    )


def _evidence(
    metric: str,
    value: float,
    signal_type: SignalType = SignalType.RIGHT_SKEWED,
) -> Evidence:
    return Evidence(
        title=f"Evidence: {metric}",
        description=f"{metric} = {value}",
        metric=metric,
        value=value,
        supporting_signal=signal_type,
        related_column="value",
    )


# ═══════════════════════════════════════════════════════════════════════
# _classify_evidence
# ═══════════════════════════════════════════════════════════════════════


class TestClassifyEvidence:
    def test_skewness_gt_0_5_is_supporting(self):
        e = _evidence("skewness", 1.2, SignalType.RIGHT_SKEWED)
        assert _classify_evidence(e) == "supporting"

    def test_skewness_zero_is_contradicting(self):
        e = _evidence("skewness", 0.0, SignalType.RIGHT_SKEWED)
        assert _classify_evidence(e) == "contradicting"

    def test_skewness_between_0_and_0_5_is_neutral(self):
        e = _evidence("skewness", 0.3, SignalType.RIGHT_SKEWED)
        assert _classify_evidence(e) == "neutral"

    def test_growth_rate_positive_is_supporting_for_increase(self):
        e = _evidence("growth_rate", 0.15, SignalType.INCREASING_TREND)
        assert _classify_evidence(e) == "supporting"

    def test_growth_rate_negative_is_contradicting_for_increase(self):
        e = _evidence("growth_rate", -0.1, SignalType.INCREASING_TREND)
        assert _classify_evidence(e) == "contradicting"

    def test_top_1_share_gt_0_5_is_supporting(self):
        e = _evidence("top_1_share", 0.75, SignalType.HIGH_CONCENTRATION)
        assert _classify_evidence(e) == "supporting"

    def test_missing_signal_type_returns_neutral(self):
        e = Evidence(
            title="test",
            description="test",
            metric="value",
            value=100,
            supporting_signal=None,
        )
        assert _classify_evidence(e) == "neutral"

    def test_unknown_metric_returns_neutral(self):
        e = _evidence("unknown_metric", 42, SignalType.RIGHT_SKEWED)
        assert _classify_evidence(e) == "neutral"

    def test_none_value_returns_neutral(self):
        e = Evidence(
            title="test",
            description="test",
            metric="skewness",
            value=None,
            supporting_signal=SignalType.RIGHT_SKEWED,
        )
        assert _classify_evidence(e) == "neutral"


# ═══════════════════════════════════════════════════════════════════════
# _determine_status
# ═══════════════════════════════════════════════════════════════════════


class TestDetermineStatus:
    def test_supporting_only_is_supported(self):
        assert _determine_status(3, 0) == HypothesisStatus.SUPPORTED

    def test_any_contradicting_is_refuted(self):
        assert _determine_status(3, 1) == HypothesisStatus.REFUTED
        assert _determine_status(0, 1) == HypothesisStatus.REFUTED

    def test_no_evidence_is_inconclusive(self):
        assert _determine_status(0, 0) == HypothesisStatus.INCONCLUSIVE


# ═══════════════════════════════════════════════════════════════════════
# validate_hypotheses — integration
# ═══════════════════════════════════════════════════════════════════════


class TestValidateHypotheses:
    def test_supported_hypothesis_with_strong_evidence(self):
        h = _hypothesis("Right skew confirmed", [SignalType.RIGHT_SKEWED])
        report = HypothesisReport(hypotheses=[h])
        evidence = [[_evidence("skewness", 1.5, SignalType.RIGHT_SKEWED)]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert vh.status == HypothesisStatus.SUPPORTED

    def test_refuted_hypothesis_with_contradicting_evidence(self):
        h = _hypothesis("Not skewed", [SignalType.RIGHT_SKEWED])
        report = HypothesisReport(hypotheses=[h])
        evidence = [[_evidence("skewness", 0.0, SignalType.RIGHT_SKEWED)]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert vh.status == HypothesisStatus.REFUTED

    def test_confidence_lowered_when_refuted(self):
        h = _hypothesis("refuted", confidence=HypothesisConfidence.HIGH)
        report = HypothesisReport(hypotheses=[h])
        evidence = [[_evidence("skewness", 0.0, SignalType.RIGHT_SKEWED)]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert vh.adjusted_confidence == HypothesisConfidence.LOW

    def test_confidence_preserved_when_supported(self):
        h = _hypothesis("supported", confidence=HypothesisConfidence.HIGH)
        report = HypothesisReport(hypotheses=[h])
        evidence = [[_evidence("skewness", 2.0, SignalType.RIGHT_SKEWED)]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert vh.adjusted_confidence == HypothesisConfidence.HIGH

    def test_inconclusive_with_no_evidence(self):
        h = _hypothesis("unknown")
        report = HypothesisReport(hypotheses=[h])
        evidence = [[]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert vh.status == HypothesisStatus.INCONCLUSIVE

    def test_evidence_distributed_correctly(self):
        """Supporting, contradicting, and neutral evidence are sorted."""
        h = _hypothesis("test")
        report = HypothesisReport(hypotheses=[h])
        evidence = [[
            _evidence("skewness", 2.0, SignalType.RIGHT_SKEWED),   # supporting
            _evidence("skewness", 0.0, SignalType.RIGHT_SKEWED),   # contradicting
            _evidence("skewness", 0.3, SignalType.RIGHT_SKEWED),   # neutral
        ]]
        result = validate_hypotheses(report, evidence)
        vh = result.validated[0]
        assert len(vh.supporting_evidence) == 1
        assert len(vh.contradicting_evidence) == 1
        assert len(vh.neutral_evidence) == 1

    def test_produces_findings(self):
        h = _hypothesis("test")
        report = HypothesisReport(hypotheses=[h])
        evidence = [[_evidence("skewness", 1.5, SignalType.RIGHT_SKEWED)]]
        result = validate_hypotheses(report, evidence)
        assert len(result.findings) == 1

    def test_parallel_inputs_matched(self):
        """Evidence list order must match hypothesis list order."""
        h1 = _hypothesis("h1", [SignalType.RIGHT_SKEWED])
        h2 = _hypothesis("h2", [SignalType.OUTLIER_DETECTED])
        report = HypothesisReport(hypotheses=[h1, h2])
        evidence = [
            [_evidence("skewness", 2.0, SignalType.RIGHT_SKEWED)],
            [_evidence("outlier_count", 5, SignalType.OUTLIER_DETECTED)],
        ]
        result = validate_hypotheses(report, evidence)
        assert result.validated[0].hypothesis.title == "h1"
        assert result.validated[1].hypothesis.title == "h2"
