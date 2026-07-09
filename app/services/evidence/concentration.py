from pandas import DataFrame

from app.schemas.profile import DatasetProfile
from app.schemas.signal import Signal
from app.models.enums import SignalType, ColumnType
from app.schemas.evidence import Evidence


def build_concentration_evidence(
    df: DataFrame,
    profile: DatasetProfile,
    signal: Signal,
) -> list[Evidence]:
    numeric_cols = [
        c.name
        for c in profile.columns
        if c.dtype == ColumnType.NUMERIC and not c.is_identifier
    ]

    evidence: list[Evidence] = []

    for num_col in numeric_cols:
        grouped = df.groupby(signal.column)[num_col].sum()
        total = grouped.sum()
        if total == 0:
            continue

        top_1 = grouped.max()
        top_1_share = top_1 / total
        top_1_cat = grouped.idxmax()

        top_n = min(3, len(grouped))
        top_n_share = grouped.nlargest(top_n).sum() / total

        evidence.append(
            Evidence(
                title=f"Top contributor in '{signal.column}' for {num_col}",
                description=(
                    f"Category '{top_1_cat}' contributes "
                    f"{top_1_share:.1%} of total {num_col}"
                ),
                metric="top_1_share",
                value=round(float(top_1_share), 4),
                supporting_signal=SignalType.HIGH_CONCENTRATION,
                related_column=signal.column,
            )
        )
        evidence.append(
            Evidence(
                title=(
                    f"Top-{top_n} concentration in '{signal.column}' "
                    f"for {num_col}"
                ),
                description=(
                    f"The top {top_n} categories contribute "
                    f"{top_n_share:.1%} of total {num_col}"
                ),
                metric=f"top_{top_n}_share",
                value=round(float(top_n_share), 4),
                supporting_signal=SignalType.HIGH_CONCENTRATION,
                related_column=signal.column,
            )
        )

    return evidence
