from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal, SignalReport
from app.models.enums import SignalType, SignalSeverity
from app.models.enums import ColumnType

def detect_signals( df: DataFrame, profile: DatasetProfile) -> SignalReport:
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
        if column.dtype != ColumnType.NUMERIC:
            continue
        series = df[column.name].dropna()
        if len (series) < 4 :
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
    return SignalReport(
        signals=signals
)