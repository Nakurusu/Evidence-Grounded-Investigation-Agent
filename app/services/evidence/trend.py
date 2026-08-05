from pandas import DataFrame

from app.models.enums import ColumnType
from app.schemas.evidence import Evidence
from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.services.statistics import compute_trend_metrics
from app.services.thresholds import (
    TREND_MIN_ABS_GROWTH_RATE,
    TREND_MIN_R_SQUARED,
    TREND_MIN_POINTS,
)


def build_trend_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    datetime_cols = [
        c.name for c in profile.columns if c.dtype == ColumnType.DATETIME
    ]
    if not datetime_cols:
        return []

    date_col = datetime_cols[0]
    metric_col = signal.metric_column or signal.column
    if metric_col is None:
        return []

    metrics = compute_trend_metrics(df, date_col, metric_col)
    if metrics is None:
        return []

    evidence = [
        Evidence(
            title=f"First value of {metric_col}",
            description=(
                f"Initial aggregated value of '{metric_col}' is "
                f"{metrics.first_value:.2f}"
            ),
            metric="first_val",
            value=round(metrics.first_value, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="date aggregation + linear trend",
            sample_size=metrics.points,
            direction="context",
        ),
        Evidence(
            title=f"Last value of {metric_col}",
            description=(
                f"Final aggregated value of '{metric_col}' is "
                f"{metrics.last_value:.2f}"
            ),
            metric="last_val",
            value=round(metrics.last_value, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="date aggregation + linear trend",
            sample_size=metrics.points,
            direction="context",
        ),
        Evidence(
            title=f"Aggregate change in {metric_col}",
            description=(
                f"'{metric_col}' changed from {metrics.first_value:.2f} to "
                f"{metrics.last_value:.2f} "
                f"(Δ={metrics.absolute_change:+.2f})"
            ),
            metric="absolute_change",
            value=round(metrics.absolute_change, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="date aggregation + linear trend",
            sample_size=metrics.points,
            direction="context",
        ),
        Evidence(
            title=f"Trend slope of {metric_col}",
            description=(
                f"Simple trend slope for '{metric_col}' is "
                f"{metrics.slope:.4f} across {metrics.points} time points"
            ),
            metric="trend_slope",
            value=round(metrics.slope, 4),
            supporting_signal=signal.type,
            related_column=metric_col,
            method="date aggregation + linear trend",
            sample_size=metrics.points,
            direction="context",
            limitation="Slope describes direction only; validation relies on growth rate and fit quality.",
        ),
        Evidence(
            title=f"Trend points for {metric_col}",
            description=(
                f"Trend analysis used {metrics.points} aggregated time points"
            ),
            metric="trend_points",
            value=metrics.points,
            supporting_signal=signal.type,
            related_column=metric_col,
            method="date aggregation + linear trend",
            threshold=TREND_MIN_POINTS,
            sample_size=metrics.points,
            direction="context",
        ),
    ]

    if metrics.r_squared is not None:
        evidence.append(
            Evidence(
                title=f"Trend fit quality for {metric_col}",
                description=(
                    f"Linear trend fit quality for '{metric_col}' is "
                    f"R²={metrics.r_squared:.3f}"
                ),
                metric="r_squared",
                value=round(metrics.r_squared, 4),
                supporting_signal=signal.type,
                related_column=metric_col,
                method="date aggregation + linear trend",
                threshold=TREND_MIN_R_SQUARED,
                sample_size=metrics.points,
                direction="context",
                strength=(
                    "moderate"
                    if metrics.r_squared >= TREND_MIN_R_SQUARED
                    else "limited"
                ),
            )
        )

    if metrics.growth_rate is not None:
        evidence.append(
            Evidence(
                title=f"Growth rate of {metric_col}",
                description=(
                    f"'{metric_col}' "
                    f"{'increased' if metrics.growth_rate > 0 else 'decreased'} by "
                    f"{abs(metrics.growth_rate):.1%} over the observed period"
                ),
                metric="growth_rate",
                value=round(metrics.growth_rate, 4),
                supporting_signal=signal.type,
                related_column=metric_col,
                method="date aggregation + linear trend",
                threshold=TREND_MIN_ABS_GROWTH_RATE,
                sample_size=metrics.points,
                direction="supporting",
                strength=(
                    "moderate"
                    if abs(metrics.growth_rate) >= TREND_MIN_ABS_GROWTH_RATE
                    else "limited"
                ),
            )
        )

    return evidence
