"""Reusable statistical calculations for investigation services."""

from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pandas import DataFrame, Series


TrendDirection = Literal["increasing", "decreasing", "flat"]


@dataclass(frozen=True)
class TrendMetrics:
    first_value: float
    last_value: float
    absolute_change: float
    growth_rate: float | None
    slope: float
    direction: TrendDirection
    points: int
    r_squared: float | None = None


@dataclass(frozen=True)
class DistributionMetrics:
    mean: float
    median: float
    std: float
    skewness: float
    count: int


@dataclass(frozen=True)
class ConcentrationMetrics:
    top_category: str
    top_1_share: float
    top_n_share: float
    top_n: int
    total: float


def compute_trend_metrics(
    df: DataFrame,
    date_column: str,
    value_column: str,
) -> TrendMetrics | None:
    """Compute trend metrics using date aggregation and a simple slope."""
    if date_column not in df.columns or value_column not in df.columns:
        return None

    working = df[[date_column, value_column]].dropna()
    if working.empty:
        return None

    working = working.copy()
    working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce")
    working = working.dropna()
    if working.empty:
        return None

    aggregated = (
        working.sort_values(date_column)
        .groupby(date_column, as_index=False)[value_column]
        .sum()
        .sort_values(date_column)
    )
    series = aggregated[value_column].dropna()
    points = int(len(series))
    if points < 2:
        return None

    first_value = float(series.iloc[0])
    last_value = float(series.iloc[-1])
    absolute_change = last_value - first_value
    growth_rate = (
        absolute_change / abs(first_value)
        if first_value != 0
        else None
    )

    x = pd.Series(range(points), dtype="float64")
    y = series.astype("float64").reset_index(drop=True)
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    denominator = float(((x - x_mean) ** 2).sum())
    slope = (
        float(((x - x_mean) * (y - y_mean)).sum() / denominator)
        if denominator != 0
        else 0.0
    )
    intercept = y_mean - slope * x_mean
    fitted = x * slope + intercept
    ss_res = float(((y - fitted) ** 2).sum())
    ss_tot = float(((y - y_mean) ** 2).sum())
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else None

    if slope > 0:
        direction: TrendDirection = "increasing"
    elif slope < 0:
        direction = "decreasing"
    else:
        direction = "flat"

    return TrendMetrics(
        first_value=first_value,
        last_value=last_value,
        absolute_change=absolute_change,
        growth_rate=float(growth_rate) if growth_rate is not None else None,
        slope=slope,
        direction=direction,
        points=points,
        r_squared=float(r_squared) if r_squared is not None else None,
    )


def compute_distribution_metrics(series: Series) -> DistributionMetrics | None:
    """Compute reusable distribution metrics for a numeric series."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 2:
        return None

    return DistributionMetrics(
        mean=float(numeric.mean()),
        median=float(numeric.median()),
        std=float(numeric.std()),
        skewness=float(numeric.skew()),
        count=int(len(numeric)),
    )


def compute_concentration_metrics(
    df: DataFrame,
    dimension_column: str,
    metric_column: str,
    top_n: int = 3,
) -> ConcentrationMetrics | None:
    """Compute top-category concentration for one dimension and one metric."""
    if dimension_column not in df.columns or metric_column not in df.columns:
        return None

    working = df[[dimension_column, metric_column]].dropna()
    if working.empty:
        return None

    values = pd.to_numeric(working[metric_column], errors="coerce")
    working = working.assign(**{metric_column: values}).dropna()
    if working.empty:
        return None

    grouped = working.groupby(dimension_column)[metric_column].sum()
    total = float(grouped.sum())
    if total == 0:
        return None

    actual_top_n = min(top_n, len(grouped))
    top_category = str(grouped.idxmax())
    top_1_share = float(grouped.max() / total)
    top_n_share = float(grouped.nlargest(actual_top_n).sum() / total)

    return ConcentrationMetrics(
        top_category=top_category,
        top_1_share=top_1_share,
        top_n_share=top_n_share,
        top_n=actual_top_n,
        total=total,
    )


def coefficient_of_variation(series: Series) -> float | None:
    """Return coefficient of variation for a numeric series."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 2:
        return None
    mean = float(numeric.mean())
    if mean == 0:
        return None
    return float(numeric.std() / abs(mean))
