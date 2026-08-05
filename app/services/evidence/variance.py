from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType
from app.schemas.evidence import Evidence
from app.services.statistics import coefficient_of_variation
from app.services.thresholds import LOW_VARIANCE_CV


def build_variance_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    series = df[signal.column].dropna()
    if len(series) < 2:
        return []

    std = float(series.std())
    cv = coefficient_of_variation(series)
    if cv is None:
        return []

    return [
        Evidence(
            title=f"Coefficient of variation for {signal.column}",
            description=(
                f"Coefficient of variation of '{signal.column}' is "
                f"{cv:.2%}"
            ),
            metric="coefficient_of_variation",
            value=round(cv, 4),
            supporting_signal=SignalType.LOW_VARIANCE,
            related_column=signal.column,
            method="coefficient of variation",
            threshold=LOW_VARIANCE_CV,
            sample_size=len(series),
            direction="supporting",
            strength="moderate" if cv <= LOW_VARIANCE_CV else "limited",
        ),
        Evidence(
            title=f"Standard deviation of {signal.column}",
            description=(
                f"Standard deviation of '{signal.column}' is {std:.2f}"
            ),
            metric="std",
            value=round(std, 4),
            supporting_signal=SignalType.LOW_VARIANCE,
            related_column=signal.column,
            method="descriptive distribution statistics",
            sample_size=len(series),
            direction="context",
        ),
    ]
