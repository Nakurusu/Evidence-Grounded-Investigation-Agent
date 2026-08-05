from app.models.enums import ColumnSemanticRole, ColumnType
from app.schemas.profile import ColumnProfile, DatasetProfile


def select_metric_columns(profile: DatasetProfile) -> list[str]:
    return [
        column.name
        for column in profile.columns
        if column.semantic_role == ColumnSemanticRole.METRIC
        and column.dtype == ColumnType.NUMERIC
        and not column.is_identifier
    ]


def select_dimension_columns(profile: DatasetProfile) -> list[str]:
    return [
        column.name
        for column in profile.columns
        if column.semantic_role == ColumnSemanticRole.DIMENSION
        and column.dtype in (
            ColumnType.CATEGORICAL,
            ColumnType.TEXT,
            ColumnType.BOOLEAN,
        )
        and not column.is_identifier
    ]


def select_entity_columns(profile: DatasetProfile) -> list[str]:
    return [
        column.name
        for column in profile.columns
        if column.semantic_role == ColumnSemanticRole.ENTITY
        and not column.is_identifier
    ]


def _time_sort_key(column: ColumnProfile) -> tuple[float, int, str]:
    return (
        column.null_percentage,
        -column.unique_count,
        column.name,
    )


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
        if column.semantic_role == ColumnSemanticRole.TIME
        and column.dtype == ColumnType.DATETIME
        and not column.is_identifier
    ]
    if candidates:
        candidates.sort(key=_time_sort_key)
        return candidates[0].name

    fallback_candidates = [
        column
        for column in profile.columns
        if column.dtype == ColumnType.DATETIME and not column.is_identifier
    ]
    if not fallback_candidates:
        return None

    fallback_candidates.sort(key=_time_sort_key)
    return fallback_candidates[0].name
