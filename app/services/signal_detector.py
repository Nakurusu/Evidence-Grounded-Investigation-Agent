from pandas import DataFrame

from app.models.enums import ColumnType, SignalSeverity, SignalType
from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal, SignalReport
from app.services.column_selection import select_trend_date_column
from app.services.statistics import (
    coefficient_of_variation,
    compute_concentration_metrics,
    compute_distribution_metrics,
    compute_trend_metrics,
)
from app.services.thresholds import (
    CONCENTRATION_TOP1_HIGH,
    HIGH_CARDINALITY_RATIO,
    LOW_VARIANCE_CV,
    MISSING_RATE_WARNING,
    OUTLIER_IQR_MULTIPLIER,
    OUTLIER_MIN_SAMPLE_SIZE,
    SKEWNESS_WARNING_ABS,
    TREND_MIN_ABS_GROWTH_RATE,
    TREND_MIN_R_SQUARED,
    TREND_MIN_POINTS,
    TREND_RELIABILITY_MIN_POINTS,
    TREND_STRONG_ABS_GROWTH_RATE,
)


def detect_signals(df: DataFrame, profile: DatasetProfile) -> SignalReport:
    signals = []
    signals.extend(detect_missing_rate(profile))
    signals.extend(detect_cardinality(profile))
    signals.extend(detect_outliers(df, profile))
    signals.extend(detect_trends(df, profile))
    signals.extend(detect_concentration(df, profile))
    signals.extend(detect_distribution(df, profile))

    return SignalReport(signals=signals)


def detect_missing_rate(profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if column.is_identifier:
            continue
        if column.null_percentage > MISSING_RATE_WARNING:
            signals.append(
                Signal(
                    type=SignalType.HIGH_MISSING_RATE,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    metric_column=column.name,
                    statistics={
                        "null_percentage": round(column.null_percentage, 4),
                        "null_count": column.null_count,
                    },
                    message=(
                        f"{column.name} has "
                        f"{column.null_percentage:.1f}% "
                        f"missing values"
                    ),
                )
            )
    return signals


def detect_cardinality(profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if column.is_identifier:
            continue
        unique_ratio = (
            column.unique_count / profile.row_count
            if profile.row_count > 0
            else 0
        )
        if (
            column.dtype in (ColumnType.TEXT, ColumnType.CATEGORICAL)
            and unique_ratio > HIGH_CARDINALITY_RATIO
        ):
            signals.append(
                Signal(
                    type=SignalType.HIGH_CARDINALITY,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    dimension_column=column.name,
                    statistics={
                        "unique_count": column.unique_count,
                        "unique_ratio": round(unique_ratio, 4),
                    },
                    message=(
                        f"{column.name} has "
                        f"{column.unique_count} unique values "
                        f"out of {profile.row_count} total rows"
                    ),
                )
            )
    return signals


def detect_outliers(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if column.is_identifier or column.dtype != ColumnType.NUMERIC:
            continue
        series = df[column.name].dropna()
        if len(series) < OUTLIER_MIN_SAMPLE_SIZE:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - OUTLIER_IQR_MULTIPLIER * iqr
        upper = q3 + OUTLIER_IQR_MULTIPLIER * iqr

        outlier_count = int(((series < lower) | (series > upper)).sum())
        if outlier_count > 0:
            outlier_ratio = outlier_count / len(series)
            signals.append(
                Signal(
                    type=SignalType.OUTLIER_DETECTED,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    metric_column=column.name,
                    statistics={
                        "outlier_count": outlier_count,
                        "outlier_ratio": round(outlier_ratio, 4),
                        "iqr_lower_bound": round(float(lower), 4),
                        "iqr_upper_bound": round(float(upper), 4),
                    },
                    message=(
                        f"{outlier_count} outliers detected in "
                        f"{column.name} using IQR method"
                    ),
                )
            )
    return signals


def detect_trends(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    numeric_columns = [
        c.name
        for c in profile.columns
        if c.dtype == ColumnType.NUMERIC and not c.is_identifier
    ]
    date_column = select_trend_date_column(profile)
    if date_column is None or not numeric_columns:
        return []
    for numeric_column in numeric_columns:
        metrics = compute_trend_metrics(df, date_column, numeric_column)
        if metrics is None or metrics.points < TREND_MIN_POINTS:
            continue

        abs_growth = (
            abs(metrics.growth_rate)
            if metrics.growth_rate is not None
            else None
        )
        has_meaningful_growth = (
            abs_growth is not None
            and abs_growth >= TREND_MIN_ABS_GROWTH_RATE
        )
        has_reliable_fit = (
            metrics.points < TREND_RELIABILITY_MIN_POINTS
            or (
                metrics.r_squared is not None
                and metrics.r_squared >= TREND_MIN_R_SQUARED
            )
        )
        if not has_meaningful_growth or not has_reliable_fit:
            continue

        severity = (
            SignalSeverity.WARNING
            if abs_growth is not None and abs_growth >= TREND_STRONG_ABS_GROWTH_RATE
            else SignalSeverity.INFO
        )

        statistics = {
            "first_val": round(metrics.first_value, 4),
            "last_val": round(metrics.last_value, 4),
            "absolute_change": round(metrics.absolute_change, 4),
            "trend_slope": round(metrics.slope, 4),
            "trend_points": metrics.points,
            "date_column": date_column,
        }
        if metrics.r_squared is not None:
            statistics["r_squared"] = round(metrics.r_squared, 4)
        if metrics.growth_rate is not None:
            statistics["growth_rate"] = round(metrics.growth_rate, 4)

        if metrics.direction == "increasing":
            signal_type = SignalType.INCREASING_TREND
            direction_text = "increasing"
        elif metrics.direction == "decreasing":
            signal_type = SignalType.DECREASING_TREND
            direction_text = "decreasing"
        else:
            continue

        signals.append(
            Signal(
                type=signal_type,
                severity=severity,
                column=numeric_column,
                metric_column=numeric_column,
                statistics=statistics,
                message=(
                    f"Column '{numeric_column}' shows a {direction_text} trend "
                    f"over {metrics.points} aggregated time points"
                ),
            )
        )
    return signals


def detect_concentration(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    categorical_columns = [
        c.name
        for c in profile.columns
        if c.dtype in (ColumnType.CATEGORICAL, ColumnType.TEXT)
        and not c.is_identifier
    ]
    numeric_columns = [
        c.name
        for c in profile.columns
        if c.dtype == ColumnType.NUMERIC and not c.is_identifier
    ]
    if not categorical_columns or not numeric_columns:
        return []

    for categorical_column in categorical_columns:
        for numeric_column in numeric_columns:
            metrics = compute_concentration_metrics(
                df, categorical_column, numeric_column
            )
            if metrics is None:
                continue

            if metrics.top_1_share > CONCENTRATION_TOP1_HIGH:
                signals.append(
                    Signal(
                        type=SignalType.HIGH_CONCENTRATION,
                        severity=SignalSeverity.WARNING,
                        column=categorical_column,
                        dimension_column=categorical_column,
                        metric_column=numeric_column,
                        statistics={
                            "top_1_share": round(metrics.top_1_share, 4),
                            "top_category": metrics.top_category,
                            "top_n_share": round(metrics.top_n_share, 4),
                            "top_n": metrics.top_n,
                            "total": round(metrics.total, 4),
                        },
                        message=(
                            f"Category '{metrics.top_category}' in column "
                            f"'{categorical_column}' contributes "
                            f"{metrics.top_1_share:.1%} of total "
                            f"'{numeric_column}'"
                        ),
                    )
                )
    return signals


def detect_distribution(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    numeric_columns = [
        c.name
        for c in profile.columns
        if c.dtype == ColumnType.NUMERIC and not c.is_identifier
    ]

    for numeric_column in numeric_columns:
        metrics = compute_distribution_metrics(df[numeric_column])
        if metrics is None:
            continue

        statistics = {
            "mean": round(metrics.mean, 4),
            "median": round(metrics.median, 4),
            "std": round(metrics.std, 4),
            "skewness": round(metrics.skewness, 4),
            "count": metrics.count,
        }

        if metrics.skewness > SKEWNESS_WARNING_ABS:
            signals.append(
                Signal(
                    type=SignalType.RIGHT_SKEWED,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    metric_column=numeric_column,
                    statistics=statistics,
                    message=(
                        f"Column '{numeric_column}' is right skewed with "
                        f"skewness {metrics.skewness:.3f}"
                    ),
                )
            )

        elif metrics.skewness < -SKEWNESS_WARNING_ABS:
            signals.append(
                Signal(
                    type=SignalType.LEFT_SKEWED,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    metric_column=numeric_column,
                    statistics=statistics,
                    message=(
                        f"Column '{numeric_column}' is left skewed with "
                        f"skewness {metrics.skewness:.3f}"
                    ),
                )
            )

        cv = coefficient_of_variation(df[numeric_column])
        if cv is not None and cv < LOW_VARIANCE_CV:
            signals.append(
                Signal(
                    type=SignalType.LOW_VARIANCE,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    metric_column=numeric_column,
                    statistics={"coefficient_of_variation": round(cv, 4)},
                    message=(
                        f"Column '{numeric_column}' has low variance with "
                        f"coefficient of variation {cv:.2%}"
                    ),
                )
            )

    return signals
