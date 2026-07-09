from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType
from app.schemas.evidence import Evidence


def build_variance_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    series = df[signal.column].dropna()
    if len(series) < 2:
        return []

    mean = float(series.mean())
    std = float(series.std())
    cv = round(std / abs(mean), 4) if mean != 0 else 0.0

    return [
        Evidence(
            title=f"Coefficient of variation for {signal.column}",
            description=(
                f"Coefficient of variation of '{signal.column}' is "
                f"{cv:.2%}"
            ),
            metric="coefficient_of_variation",
            value=cv,
            supporting_signal=SignalType.LOW_VARIANCE,
            related_column=signal.column,
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
        ),
    ]
