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
from app.models.enums import SignalType
from app.schemas.evidence import EvidenceReport, Evidence

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


def generate_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal_report: SignalReport,
) -> EvidenceReport:
    evidence: list[Evidence] = []
    for signal in signal_report.signals:
        builder = EVIDENCE_BUILDERS.get(signal.type)
        if builder is None:
            continue
        evidence.extend(builder(df, profile, signal))
    return EvidenceReport(evidence=evidence)
