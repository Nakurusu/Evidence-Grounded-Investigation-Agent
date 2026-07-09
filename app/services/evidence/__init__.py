from app.services.evidence.concentration import build_concentration_evidence
from app.services.evidence.distribution import build_distribution_evidence
from app.services.evidence.outlier import build_outlier_evidence
from app.services.evidence.trend import build_trend_evidence
from app.services.evidence.missing_rate import build_missing_rate_evidence
from app.services.evidence.cardinality import build_cardinality_evidence
from app.services.evidence.variance import build_variance_evidence

from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import SignalReport
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.models.enums import SignalType
from app.schemas.evidence import Evidence

EVIDENCE_BUILDERS = {
    SignalType.HIGH_CONCENTRATION: build_concentration_evidence,
    SignalType.RIGHT_SKEWED: build_distribution_evidence,
    SignalType.LEFT_SKEWED: build_distribution_evidence,
    SignalType.OUTLIER_DETECTED: build_outlier_evidence,
    SignalType.INCREASING_TREND: build_trend_evidence,
    SignalType.DECREASING_TREND: build_trend_evidence,
    SignalType.HIGH_MISSING_RATE: build_missing_rate_evidence,
    SignalType.HIGH_CARDINALITY: build_cardinality_evidence,
    SignalType.LOW_VARIANCE: build_variance_evidence,
}


def generate_evidence_for_hypothesis(
    df: DataFrame,
    profile: DatasetProfile,
    hypothesis: Hypothesis,
    signal_report: SignalReport,
) -> list[Evidence]:
    """Extract evidence relevant to validating a single hypothesis."""
    relevant_signals = [
        s for s in signal_report.signals
        if s.type in hypothesis.supporting_signals
    ]

    evidence: list[Evidence] = []
    for signal in relevant_signals:
        builder = EVIDENCE_BUILDERS.get(signal.type)
        if builder is None:
            continue
        evidence.extend(builder(df, profile, signal))
    return evidence


def generate_all_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    hypothesis_report: HypothesisReport,
    signal_report: SignalReport,
) -> list[list[Evidence]]:
    """Extract evidence for every hypothesis.

    Returns a list parallel to hypothesis_report.hypotheses, where each
    element is the evidence collected for the corresponding hypothesis.
    """
    return [
        generate_evidence_for_hypothesis(df, profile, h, signal_report)
        for h in hypothesis_report.hypotheses
    ]
