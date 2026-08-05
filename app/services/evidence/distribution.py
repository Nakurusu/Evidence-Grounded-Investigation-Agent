from pandas import DataFrame

from app.schemas.evidence import Evidence
from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.services.statistics import compute_distribution_metrics
from app.services.thresholds import SKEWNESS_WARNING_ABS


def build_distribution_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    metric_col = signal.metric_column or signal.column
    if metric_col is None or metric_col not in df.columns:
        return []

    metrics = compute_distribution_metrics(df[metric_col])
    if metrics is None:
        return []

    return [
        Evidence(
            title=f"Mean value of {metric_col}",
            description=f"Mean of '{metric_col}' is {metrics.mean:.2f}",
            metric="mean",
            value=round(metrics.mean, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="descriptive distribution statistics",
            sample_size=metrics.count,
            direction="context",
        ),
        Evidence(
            title=f"Median value of {metric_col}",
            description=f"Median of '{metric_col}' is {metrics.median:.2f}",
            metric="median",
            value=round(metrics.median, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="descriptive distribution statistics",
            sample_size=metrics.count,
            direction="context",
        ),
        Evidence(
            title=f"Standard deviation of {metric_col}",
            description=(
                f"Standard deviation of '{metric_col}' is {metrics.std:.2f}"
            ),
            metric="std",
            value=round(metrics.std, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="descriptive distribution statistics",
            sample_size=metrics.count,
            direction="context",
        ),
        Evidence(
            title=f"Skewness of {metric_col}",
            description=(
                f"Skewness coefficient of '{metric_col}' is "
                f"{metrics.skewness:.3f}"
            ),
            metric="skewness",
            value=round(metrics.skewness, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="sample skewness",
            threshold=SKEWNESS_WARNING_ABS,
            sample_size=metrics.count,
            direction="supporting",
            strength=(
                "moderate"
                if abs(metrics.skewness) >= SKEWNESS_WARNING_ABS
                else "limited"
            ),
        ),
        Evidence(
            title=f"Observation count for {metric_col}",
            description=(
                f"Distribution analysis used {metrics.count} valid values"
            ),
            metric="count",
            value=metrics.count,
            supporting_signal=signal.type,
            related_column=metric_col,
            method="descriptive distribution statistics",
            sample_size=metrics.count,
            direction="context",
        ),
    ]
