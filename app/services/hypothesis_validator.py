from app.models.enums import SignalType, HypothesisStatus, HypothesisConfidence
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.schemas.evidence import Evidence
from app.schemas.validated_hypothesis import ValidatedHypothesis, ValidationReport


# ---------------------------------------------------------------------------
# Per-signal-type validation rules
#
# Each rule says: for evidence with this metric, what value range counts as
# "supporting" the hypothesis, and what range counts as "contradicting" it.
# ---------------------------------------------------------------------------

_VALIDATION_RULES: dict[SignalType, dict[str, dict]] = {
    SignalType.RIGHT_SKEWED: {
        "skewness": {
            "supporting_if": lambda v: v > 0.5,
            "contradicting_if": lambda v: v <= 0,
        },
    },
    SignalType.LEFT_SKEWED: {
        "skewness": {
            "supporting_if": lambda v: v < -0.5,
            "contradicting_if": lambda v: v >= 0,
        },
    },
    SignalType.OUTLIER_DETECTED: {
        "outlier_count": {
            "supporting_if": lambda v: v > 0,
            "contradicting_if": lambda v: v == 0,
        },
    },
    SignalType.INCREASING_TREND: {
        "growth_rate": {
            "supporting_if": lambda v: v > 0.05,
            "contradicting_if": lambda v: v <= 0,
        },
    },
    SignalType.DECREASING_TREND: {
        "growth_rate": {
            "supporting_if": lambda v: v < -0.05,
            "contradicting_if": lambda v: v >= 0,
        },
    },
    SignalType.HIGH_CONCENTRATION: {
        "top_1_share": {
            "supporting_if": lambda v: v > 0.5,
            "contradicting_if": lambda v: v <= 0.3,
        },
    },
    SignalType.HIGH_MISSING_RATE: {
        "null_percentage": {
            "supporting_if": lambda v: v > 20,
            "contradicting_if": lambda v: v <= 5,
        },
    },
    SignalType.HIGH_CARDINALITY: {
        "unique_ratio": {
            "supporting_if": lambda v: v > 0.9,
            "contradicting_if": lambda v: v <= 0.5,
        },
    },
    SignalType.LOW_VARIANCE: {
        "coefficient_of_variation": {
            "supporting_if": lambda v: v < 0.05,
            "contradicting_if": lambda v: v >= 0.1,
        },
    },
}


def _classify_evidence(evidence: Evidence) -> str:
    """Classify a single evidence item as 'supporting', 'contradicting', or 'neutral'."""
    signal_type = evidence.supporting_signal
    if signal_type is None:
        return "neutral"

    rules = _VALIDATION_RULES.get(signal_type)
    if rules is None:
        return "neutral"

    metric_name = evidence.metric
    rule = rules.get(metric_name) if metric_name else None
    if rule is None:
        return "neutral"

    value = evidence.value
    if value is None:
        return "neutral"

    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return "neutral"

    if rule["supporting_if"](numeric_value):
        return "supporting"
    if rule["contradicting_if"](numeric_value):
        return "contradicting"
    return "neutral"


def _determine_status(
    supporting_count: int,
    contradicting_count: int,
    total: int,
) -> HypothesisStatus:
    if total == 0:
        return HypothesisStatus.INCONCLUSIVE

    if contradicting_count > 0:
        return HypothesisStatus.REFUTED

    if supporting_count > total * 0.5:
        return HypothesisStatus.SUPPORTED

    return HypothesisStatus.INCONCLUSIVE


def _adjusted_confidence(
    original: HypothesisConfidence,
    status: HypothesisStatus,
) -> HypothesisConfidence:
    if status == HypothesisStatus.REFUTED:
        return HypothesisConfidence.LOW
    return original


def validate_hypotheses(
    hypothesis_report: HypothesisReport,
    evidence_by_hypothesis: list[list[Evidence]],
) -> ValidationReport:
    """Validate every hypothesis against its collected evidence.

    Args:
        hypothesis_report: All generated hypotheses.
        evidence_by_hypothesis: Evidence for each hypothesis, in the same
            order as hypothesis_report.hypotheses.

    Returns:
        ValidationReport with one ValidatedHypothesis per input hypothesis.
    """
    validated: list[ValidatedHypothesis] = []

    for hypothesis, evidence_list in zip(
        hypothesis_report.hypotheses, evidence_by_hypothesis
    ):
        supporting: list[Evidence] = []
        contradicting: list[Evidence] = []

        for e in evidence_list:
            label = _classify_evidence(e)
            if label == "supporting":
                supporting.append(e)
            elif label == "contradicting":
                contradicting.append(e)

        status = _determine_status(
            len(supporting), len(contradicting), len(evidence_list)
        )

        validated.append(
            ValidatedHypothesis(
                hypothesis=hypothesis,
                status=status,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                adjusted_confidence=_adjusted_confidence(
                    hypothesis.confidence, status
                ),
            )
        )

    return ValidationReport(validated=validated)
