from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal, SignalReport
from app.models.enums import SignalType, SignalSeverity
from app.models.enums import ColumnType

def detect_signals( df: DataFrame, profile: DatasetProfile) -> SignalReport:
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

def detect_cardinality(profile: DatasetProfile) -> list[Signal]:
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
        if len(series) < 4:
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
    signals = []
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
    for numeric_column in numeric_columns:
        series = df_sorted[numeric_column].dropna()
        if len(series) < 2:
            continue
        first = series.iloc[0]
        last = series.iloc[-1]
        if last > first * 1.2:
            signals.append(
                Signal(
                    type=SignalType.INCREASING_TREND,
                    severity=SignalSeverity.INFO,
                        column=numeric_column,
                        message=(
                            f"{numeric_column} shows an increasing trend "
                            f"over time based on the first and last values"
                        )
                    )
            )
        elif last < first * 0.8:
            signals.append(
                Signal(
                    type=SignalType.DECREASING_TREND,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    message=(
                        f"{numeric_column} shows a decreasing trend "
                        f"over time based on the first and last values"
                    )
                )
            )
    return signals

    
def detect_concentration(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    categorical_columns = [
        c.name for c in profile.columns if c.dtype == ColumnType.CATEGORICAL
    ]
    numeric_columns = [
        c.name for c in profile.columns if c.dtype == ColumnType.NUMERIC
    ]
    if not categorical_columns or not numeric_columns:
        return []
    
    categorical_column = categorical_columns[0]
    numeric_column = numeric_columns[0]

    grouped = df.groupby(categorical_column)[numeric_column].sum()
    # TODO: Analyze all numeric columns
    total = grouped.sum()

    if total == 0:
        return []
    
    top_share = grouped.max() / total
    top_category = grouped.idxmax()

    if top_share > 0.7:
        signals.append(
            Signal(
                type=SignalType.HIGH_CONCENTRATION,
                severity=SignalSeverity.WARNING,
                column=categorical_column,
                message=(
                    f"{top_category} contributes "
                    f"{top_share:.1%} of total {numeric_column}"
                )
            )
        )
    return []

def detect_distribution(df: DataFrame, profile: DatasetProfile) -> list[Signal]:
    signals = []
    numeric_columns = [
        c.name for c in profile.columns if c.dtype == ColumnType.NUMERIC
    ]

    if not numeric_columns:
        return []

    for numeric_column in numeric_columns:
        series = df[numeric_column].dropna()

        if len(series) < 2:
            continue

        mean = series.mean()
        median = series.median()

        if mean > median * 1.2:
            signals.append(
                Signal(
                    type=SignalType.RIGHT_SKEWED,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    message=(
                        f"{numeric_column} is right skewed with mean "
                        f"{mean:.2f} and median {median:.2f}"
                    )
                )
            )

        if mean < median * 0.8:
            signals.append(
                Signal(
                    type=SignalType.LEFT_SKEWED,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    message=(
                        f"{numeric_column} is left skewed with mean "
                        f"{mean:.2f} and median {median:.2f}"
                    )
                )
            )

        std = series.std()

        if mean == 0:
            continue

        coefficient_of_variation = std / abs(mean)

        if coefficient_of_variation < 0.05:
            signals.append(
                Signal(
                    type=SignalType.LOW_VARIANCE,
                    severity=SignalSeverity.INFO,
                    column=numeric_column,
                    message=(
                        f"{numeric_column} has low variance with "
                        f"coefficient of variation {coefficient_of_variation:.2%}"
                    )
                )
            )

    return signals