from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.schemas.evidence import Evidence


def build_distribution_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    series = df[signal.column].dropna()
    if len(series) < 2:
        return []

    mean = float(series.mean())
    median = float(series.median())
    std = float(series.std())
    skew = float(series.skew())

    return [
        Evidence(
            title=f"Mean value of {signal.column}",
            description=f"Mean of '{signal.column}' is {mean:.2f}",
            metric="mean",
            value=round(mean, 4),
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
        Evidence(
            title=f"Median value of {signal.column}",
            description=f"Median of '{signal.column}' is {median:.2f}",
            metric="median",
            value=round(median, 4),
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
        Evidence(
            title=f"Standard deviation of {signal.column}",
            description=(
                f"Standard deviation of '{signal.column}' is {std:.2f}"
            ),
            metric="std",
            value=round(std, 4),
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
        Evidence(
            title=f"Skewness of {signal.column}",
            description=(
                f"Skewness coefficient of '{signal.column}' is {skew:.3f}"
            ),
            metric="skewness",
            value=round(skew, 4),
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
    ]
