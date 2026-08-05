from pandas import DataFrame

from app.models.enums import SignalType
from app.schemas.evidence import Evidence
from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.services.column_selection import select_metric_columns
from app.services.statistics import compute_concentration_metrics
from app.services.thresholds import CONCENTRATION_TOP1_WARNING


def build_concentration_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    dimension_col = signal.dimension_column or signal.column
    if dimension_col is None:
        return []

    metric_cols = (
        [signal.metric_column]
        if signal.metric_column
        else select_metric_columns(profile)
    )

    evidence: list[Evidence] = []
    for metric_col in metric_cols:
        if metric_col is None:
            continue

        metrics = compute_concentration_metrics(df, dimension_col, metric_col)
        if metrics is None:
            continue

        evidence.append(
            Evidence(
                title=f"Top contributor in '{dimension_col}' for {metric_col}",
                description=(
                    f"Category '{metrics.top_category}' contributes "
                    f"{metrics.top_1_share:.1%} of total {metric_col}"
                ),
                metric="top_1_share",
                value=round(metrics.top_1_share, 4),
                supporting_signal=SignalType.HIGH_CONCENTRATION,
                related_column=metric_col,
                method="category aggregation concentration",
                threshold=CONCENTRATION_TOP1_WARNING,
                sample_size=len(df[[dimension_col, metric_col]].dropna()),
                direction="supporting",
                strength=(
                    "moderate"
                    if metrics.top_1_share >= CONCENTRATION_TOP1_WARNING
                    else "limited"
                ),
            )
        )
        evidence.append(
            Evidence(
                title=(
                    f"Top-{metrics.top_n} concentration in '{dimension_col}' "
                    f"for {metric_col}"
                ),
                description=(
                    f"The top {metrics.top_n} categories contribute "
                    f"{metrics.top_n_share:.1%} of total {metric_col}"
                ),
                metric=f"top_{metrics.top_n}_share",
                value=round(metrics.top_n_share, 4),
                supporting_signal=SignalType.HIGH_CONCENTRATION,
                related_column=metric_col,
                method="category aggregation concentration",
                sample_size=len(df[[dimension_col, metric_col]].dropna()),
                direction="context",
            )
        )

    return evidence
