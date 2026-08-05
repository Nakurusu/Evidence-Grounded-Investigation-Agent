from app.models.enums import ColumnType
from app.schemas.profile import DatasetProfile


def select_trend_date_column(profile: DatasetProfile) -> str | None:
    """Select the best datetime column for trend analysis.

    Prefer non-identifier datetime columns with lower missingness and more
    distinct values. This keeps the default deterministic while avoiding a
    blind dependency on dataframe column order when multiple datetime fields
    exist.
    """
    candidates = [
        column
        for column in profile.columns
        if column.dtype == ColumnType.DATETIME and not column.is_identifier
    ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda column: (
            column.null_percentage,
            -column.unique_count,
            column.name,
        )
    )
    return candidates[0].name
