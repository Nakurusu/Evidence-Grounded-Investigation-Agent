from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal, SignalReport
from app.models.enums import SignalType, SignalSeverity
from app.models.enums import ColumnType

def detect_signals( df: DataFrame, profile: DatasetProfile) -> SignalReport:
    signals = []
    signals.extend(detect_missing_rate(df, profile))
    signals.extend(detect_cardinality(df, profile))
    signals.extend(detect_outliers(df, profile))
    signals.extend(detect_trends(df, profile))

    return SignalReport(signals=signals)


def detect_missing_rate(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if column.null_percentage > 20:
            signals.append(
                Signal(
                    type=SignalType.HIGH_MISSING_RATE,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    message=(
                        f"{column.name} has "
                        f"{column.null_percentage:.1f}% "
                        f"missing values"
                    )
                )
            )
    return signals

def detect_cardinality(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if (
            column.dtype in (
                ColumnType.TEXT,
                ColumnType.CATEGORICAL,
            )
            and profile.row_count > 0
            and column.unique_count / profile.row_count > 0.9
        ):
            signals.append(
                Signal(
                    type=SignalType.HIGH_CARDINALITY,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    message=(
                        f"{column.name} has "
                        f"{column.unique_count} unique values "
                        f"out of {profile.row_count} total rows"
                    )
                )
            )
    return signals

def detect_outliers(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    for column in profile.columns:
        if column.dtype != ColumnType.NUMERIC:
            continue
        series = df[column.name].dropna()
        if len(series) < 4 :
            continue

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        
        outlier_count = (
            (series < lower) | (series > upper)
        ).sum()
        if outlier_count > 0:
            signals.append(
                Signal(
                    type=SignalType.OUTLIER_DETECTED,
                    severity=SignalSeverity.WARNING,
                    column=column.name,
                    message=(
                        f"{outlier_count} outliers detected in "
                        f"{column.name} using IQR method"
                    )
                )
            )
    return signals


def detect_trends(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    datetime_columns = [
        c.name for c in profile.columns if c.dtype == ColumnType.DATETIME
    ]
    numeric_columns = [
        c.name for c in profile.columns if c.dtype == ColumnType.NUMERIC
    ]
    if not datetime_columns or not numeric_columns:
        return []
    date_column = datetime_columns[0]
    df_sorted = df.sort_values(date_column)

    series = df_sorted[numeric_columns[0]].dropna()
    if len(series) < 2:
        return []
    first = series.iloc[0]
    last = series.iloc[-1]
    if last > first * 1.2:
        return [
            Signal(
                type=SignalType.INCREASING_TREND,
                severity=SignalSeverity.INFO,
                    column=numeric_columns[0],
                    # TODO:
                    # Analyze all numeric columns
                    message=(
                        f"{numeric_columns[0]} shows an increasing trend "
                        f"over time based on the first and last values"
                    )
                )
            ]
    elif last < first * 0.8:
        return [
            Signal(
                type=SignalType.DECREASING_TREND,
                severity=SignalSeverity.INFO,
                column=numeric_columns[0],
                message=(
                    f"{numeric_columns[0]} shows a decreasing trend "
                    f"over time based on the first and last values"
                )
            )
        ]
    else:
        return []