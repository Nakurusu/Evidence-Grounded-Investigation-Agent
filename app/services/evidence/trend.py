from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import ColumnType
from app.schemas.evidence import Evidence


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
    df_sorted = df.sort_values(date_col)
    series = df_sorted[signal.column].dropna()

    if len(series) < 2:
        return []

    first_val = float(series.iloc[0])
    last_val = float(series.iloc[-1])
    change = last_val - first_val
    growth_rate = (
        round(change / abs(first_val), 4) if first_val != 0 else 0
    )

    return [
        Evidence(
            title=f"Aggregate change in {signal.column}",
            description=(
                f"'{signal.column}' changed from {first_val:.2f} to "
                f"{last_val:.2f} (Δ={change:+.2f})"
            ),
            metric="absolute_change",
            value=round(change, 4),
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
        Evidence(
            title=f"Growth rate of {signal.column}",
            description=(
                f"'{signal.column}' "
                f"{'increased' if change > 0 else 'decreased'} by "
                f"{abs(growth_rate):.1%} over the observed period"
            ),
            metric="growth_rate",
            value=growth_rate,
            supporting_signal=signal.type,
            related_column=signal.column,
        ),
    ]
