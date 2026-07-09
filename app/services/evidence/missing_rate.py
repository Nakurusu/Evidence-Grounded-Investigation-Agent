from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType
from app.schemas.evidence import Evidence


def build_missing_rate_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    col_profile = next(
        (c for c in profile.columns if c.name == signal.column), None
    )
    if col_profile is None:
        return []

    return [
        Evidence(
            title=f"Missing rate in {signal.column}",
            description=(
                f"Column '{signal.column}' has {col_profile.null_count} "
                f"null values out of {profile.row_count} total rows "
                f"({col_profile.null_percentage:.1f}%)"
            ),
            metric="null_percentage",
            value=round(col_profile.null_percentage, 2),
            supporting_signal=SignalType.HIGH_MISSING_RATE,
            related_column=signal.column,
        ),
    ]
