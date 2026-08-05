from pandas import DataFrame

from app.models.enums import ColumnSemanticRole, ColumnType
from app.schemas.profile import DatasetProfile


def analyze_dataframe(
    df: DataFrame,
    profile: DatasetProfile,
) -> dict:

    numeric_columns = []
    categorical_columns = []
    datetime_columns = []
    boolean_columns = []
    text_columns = []
    metric_columns = []
    dimension_columns = []
    time_columns = []
    entity_columns = []
    identifier_columns = []

    for column in profile.columns:

        if column.dtype == ColumnType.NUMERIC:
            numeric_columns.append(column.name)

        elif column.dtype == ColumnType.CATEGORICAL:
            categorical_columns.append(column.name)

        elif column.dtype == ColumnType.DATETIME:
            datetime_columns.append(column.name)

        elif column.dtype == ColumnType.BOOLEAN:
            boolean_columns.append(column.name)

        elif column.dtype == ColumnType.TEXT:
            text_columns.append(column.name)

        if column.semantic_role == ColumnSemanticRole.METRIC:
            metric_columns.append(column.name)
        elif column.semantic_role == ColumnSemanticRole.DIMENSION:
            dimension_columns.append(column.name)
        elif column.semantic_role == ColumnSemanticRole.TIME:
            time_columns.append(column.name)
        elif column.semantic_role == ColumnSemanticRole.ENTITY:
            entity_columns.append(column.name)
        elif column.semantic_role == ColumnSemanticRole.IDENTIFIER:
            identifier_columns.append(column.name)

    return {
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "boolean_columns": boolean_columns,
        "text_columns": text_columns,
        "metric_columns": metric_columns,
        "dimension_columns": dimension_columns,
        "time_columns": time_columns,
        "entity_columns": entity_columns,
        "identifier_columns": identifier_columns,
    }
