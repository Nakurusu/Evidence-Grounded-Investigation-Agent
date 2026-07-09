from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType
from app.schemas.evidence import Evidence


def build_cardinality_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    col_profile = next(
        (c for c in profile.columns if c.name == signal.column), None
    )
    if col_profile is None:
        return []

    unique_ratio = (
        round(col_profile.unique_count / profile.row_count, 4)
        if profile.row_count > 0
        else 0
    )

    return [
        Evidence(
            title=f"Unique value count in {signal.column}",
            description=(
                f"Column '{signal.column}' has {col_profile.unique_count} "
                f"unique values out of {profile.row_count} total rows"
            ),
            metric="unique_count",
            value=col_profile.unique_count,
            supporting_signal=SignalType.HIGH_CARDINALITY,
            related_column=signal.column,
        ),
        Evidence(
            title=f"Uniqueness ratio in {signal.column}",
            description=(
                f"Column '{signal.column}' has a uniqueness ratio of "
                f"{unique_ratio:.1%}"
            ),
            metric="unique_ratio",
            value=unique_ratio,
            supporting_signal=SignalType.HIGH_CARDINALITY,
            related_column=signal.column,
        ),
    ]
