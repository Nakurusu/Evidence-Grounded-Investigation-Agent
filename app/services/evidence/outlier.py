from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType
from app.schemas.evidence import Evidence
from app.services.thresholds import (
    OUTLIER_IQR_MULTIPLIER,
    OUTLIER_MIN_SAMPLE_SIZE,
)


def build_outlier_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    series = df[signal.column].dropna()
    if len(series) < OUTLIER_MIN_SAMPLE_SIZE:
        return []

    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - OUTLIER_IQR_MULTIPLIER * IQR
    upper = Q3 + OUTLIER_IQR_MULTIPLIER * IQR

    outlier_mask = (series < lower) | (series > upper)
    outlier_count = int(outlier_mask.sum())
    outlier_ratio = (
        round(outlier_count / len(series), 4) if len(series) > 0 else 0
    )

    return [
        Evidence(
            title=f"Outlier count in {signal.column}",
            description=(
                f"{outlier_count} outliers detected in '{signal.column}' "
                f"({outlier_ratio:.1%} of non-null values)"
            ),
            metric="outlier_count",
            value=outlier_count,
            supporting_signal=SignalType.OUTLIER_DETECTED,
            related_column=signal.column,
            method="IQR outlier detection",
            threshold=(
                f"outside [Q1 - {OUTLIER_IQR_MULTIPLIER}×IQR, "
                f"Q3 + {OUTLIER_IQR_MULTIPLIER}×IQR]"
            ),
            sample_size=len(series),
            direction="supporting",
            strength="moderate" if outlier_count > 0 else "limited",
        ),
        Evidence(
            title=f"Outlier ratio in {signal.column}",
            description=(
                f"Outliers represent {outlier_ratio:.1%} of non-null "
                f"values in '{signal.column}'"
            ),
            metric="outlier_ratio",
            value=outlier_ratio,
            supporting_signal=SignalType.OUTLIER_DETECTED,
            related_column=signal.column,
            method="IQR outlier detection",
            sample_size=len(series),
            direction="context",
        ),
        Evidence(
            title=f"IQR lower bound for {signal.column}",
            description=(
                f"Values below {lower:.2f} are considered outliers "
                f"in '{signal.column}'"
            ),
            metric="iqr_lower_bound",
            value=round(float(lower), 4),
            supporting_signal=SignalType.OUTLIER_DETECTED,
            related_column=signal.column,
            method="IQR outlier detection",
            sample_size=len(series),
            direction="context",
        ),
        Evidence(
            title=f"IQR upper bound for {signal.column}",
            description=(
                f"Values above {upper:.2f} are considered outliers "
                f"in '{signal.column}'"
            ),
            metric="iqr_upper_bound",
            value=round(float(upper), 4),
            supporting_signal=SignalType.OUTLIER_DETECTED,
            related_column=signal.column,
            method="IQR outlier detection",
            sample_size=len(series),
            direction="context",
        ),
    ]
