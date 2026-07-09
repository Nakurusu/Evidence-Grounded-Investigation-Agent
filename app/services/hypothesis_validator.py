from app.models.enums import SignalType, HypothesisStatus, HypothesisConfidence
from app.schemas.hypothesis import HypothesisReport
from app.schemas.evidence import Evidence
from app.schemas.validated_hypothesis import (
    ValidatedHypothesis,
    ValidatedHypothesisReport,
    Finding,
)


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
) -> HypothesisStatus:
    """Determine hypothesis status from classified evidence counts.

    Only evidence items that matched a validation rule are counted.
    Neutral items (no matching rule) are excluded.
    """
    if supporting_count == 0 and contradicting_count == 0:
        return HypothesisStatus.INCONCLUSIVE

    if contradicting_count > 0:
        return HypothesisStatus.REFUTED

    # At least one supporting and zero contradicting
    return HypothesisStatus.SUPPORTED


def _adjusted_confidence(
    original: HypothesisConfidence,
    status: HypothesisStatus,
) -> HypothesisConfidence:
    if status == HypothesisStatus.REFUTED:
        return HypothesisConfidence.LOW
    return original


def _build_finding(vh: ValidatedHypothesis) -> Finding:
    """Build a self-contained summary of one validated hypothesis for LLM consumption."""
    supporting_metrics = {
        e.metric: float(e.value)
        for e in vh.supporting_evidence
        if e.metric is not None and e.value is not None
    }
    contradicting_metrics = {
        e.metric: float(e.value)
        for e in vh.contradicting_evidence
        if e.metric is not None and e.value is not None
    }

    title = vh.hypothesis.title
    status = vh.status

    if status == HypothesisStatus.SUPPORTED:
        summary = (
            f"Hypothesis '{title}' is SUPPORTED by the evidence. "
            f"Key metrics: {_format_metrics(supporting_metrics)}. "
            f"Confidence: {vh.adjusted_confidence.value}."
        )
    elif status == HypothesisStatus.REFUTED:
        summary = (
            f"Hypothesis '{title}' is REFUTED. "
            f"Contradicting evidence: {_format_metrics(contradicting_metrics)}. "
            f"Confidence lowered to {vh.adjusted_confidence.value}."
        )
    else:
        summary = (
            f"Hypothesis '{title}' is INCONCLUSIVE — "
            f"insufficient or mixed evidence to validate or refute. "
            f"Confidence remains at {vh.adjusted_confidence.value}."
        )

    return Finding(
        hypothesis_title=title,
        status=status,
        summary=summary,
        supporting_metrics=supporting_metrics,
        contradicting_metrics=contradicting_metrics,
    )


def _format_metrics(metrics: dict[str, float]) -> str:
    """Format a metrics dict as a human-readable string."""
    return ", ".join(
        f"{name}={value:.3g}" for name, value in metrics.items()
    )


def validate_hypotheses(
    hypothesis_report: HypothesisReport,
    evidence_by_hypothesis: list[list[Evidence]],
) -> ValidatedHypothesisReport:
    """Validate every hypothesis against its collected evidence.

    Args:
        hypothesis_report: All generated hypotheses.
        evidence_by_hypothesis: Evidence for each hypothesis, in the same
            order as hypothesis_report.hypotheses.

    Returns:
        ValidatedHypothesisReport with validated hypotheses and LLM-ready findings.
    """
    validated: list[ValidatedHypothesis] = []

    for hypothesis, evidence_list in zip(
        hypothesis_report.hypotheses, evidence_by_hypothesis
    ):
        supporting: list[Evidence] = []
        contradicting: list[Evidence] = []
        neutral: list[Evidence] = []

        for e in evidence_list:
            label = _classify_evidence(e)
            if label == "supporting":
                supporting.append(e)
            elif label == "contradicting":
                contradicting.append(e)
            else:
                neutral.append(e)

        status = _determine_status(
            len(supporting), len(contradicting)
        )

        validated.append(
            ValidatedHypothesis(
                hypothesis=hypothesis,
                status=status,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                neutral_evidence=neutral,
                adjusted_confidence=_adjusted_confidence(
                    hypothesis.confidence, status
                ),
            )
        )

    findings = [_build_finding(vh) for vh in validated]

    return ValidatedHypothesisReport(validated=validated, findings=findings)
