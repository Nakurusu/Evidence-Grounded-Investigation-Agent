from dataclasses import dataclass, field

from pandas import DataFrame
import pandas as pd
from app.schemas.profile import DatasetProfile, ColumnProfile
from app.models.enums import ColumnSemanticRole, ColumnType

IDENTIFIER_KEYWORDS = {
    "id",
    "uuid",
    "key",
    "identifier",
    "name",
    "email",
    "phone",
    "mobile",
    "account"
}

ENTITY_KEYWORDS = {
    "customer",
    "client",
    "user",
    "product",
    "order",
    "account",
    "vendor",
    "supplier",
    "store",
    "merchant",
    "employee",
}


@dataclass(frozen=True)
class ProfilerRules:
    categorical_unique_ratio: float = 0.5
    identifier_unique_ratio: float = 0.95
    entity_unique_ratio: float = 0.5
    identifier_keywords: set[str] = field(
        default_factory=lambda: set(IDENTIFIER_KEYWORDS)
    )
    entity_keywords: set[str] = field(
        default_factory=lambda: set(ENTITY_KEYWORDS)
    )


DEFAULT_PROFILER_RULES = ProfilerRules()


def profile_dataframe(
    df: DataFrame,
    rules: ProfilerRules | None = None,
) -> DatasetProfile:
    active_rules = rules or DEFAULT_PROFILER_RULES
    row_count = len(df)
    column_count = len(df.columns)
    column_profiles = []
    for column in df.columns:
        dtype = infer_column_type(df[column], active_rules)
        is_identifier = detect_identifiers(column, df[column], active_rules)
        null_count = int(df[column].isna().sum())
        null_percentage = (
            null_count / row_count * 100
            if row_count > 0
            else 0
        )
        unique_count = int(df[column].nunique())
        column_profiles.append(
            ColumnProfile(
                name=column,
                dtype=dtype,
                semantic_role=infer_semantic_role(
                    column,
                    df[column],
                    dtype,
                    is_identifier,
                    active_rules,
                ),
                is_identifier=is_identifier,
                null_count=null_count,
                null_percentage=null_percentage,
                unique_count=unique_count
            )
        )
    return DatasetProfile(
        row_count=row_count,
        column_count=column_count,
        columns=column_profiles
    )

def infer_column_type(
    series,
    rules: ProfilerRules | None = None,
) -> ColumnType:
    active_rules = rules or DEFAULT_PROFILER_RULES
    if pd.api.types.is_bool_dtype(series):
        return ColumnType.BOOLEAN
    if pd.api.types.is_numeric_dtype(series):
        return ColumnType.NUMERIC
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnType.DATETIME
    series_non_null = series.dropna()

    if len(series_non_null) > 0:
        try:
            pd.to_datetime(
                series_non_null,
                errors="raise",
                format="mixed",
            )
            return ColumnType.DATETIME
        except Exception:
            pass
            
    unique_ratio = unique_value_ratio(series)
    if unique_ratio < active_rules.categorical_unique_ratio:
        return ColumnType.CATEGORICAL
    else:
        return ColumnType.TEXT
    
def unique_value_ratio(series) -> float:
    non_null = series.dropna()
    return non_null.nunique() / len(non_null) if len(non_null) > 0 else 0

def detect_identifiers(
    column_name,
    series,
    rules: ProfilerRules | None = None,
) -> bool:
    active_rules = rules or DEFAULT_PROFILER_RULES
    unique_ratio = unique_value_ratio(series)
    return unique_ratio > active_rules.identifier_unique_ratio and any(
        keyword in column_name.lower()
        for keyword in active_rules.identifier_keywords
    )


def infer_semantic_role(
    column_name: str,
    series,
    dtype: ColumnType,
    is_identifier: bool,
    rules: ProfilerRules | None = None,
) -> ColumnSemanticRole:
    active_rules = rules or DEFAULT_PROFILER_RULES
    lowered_name = column_name.lower()
    unique_ratio = unique_value_ratio(series)

    if is_identifier:
        return ColumnSemanticRole.IDENTIFIER

    if dtype == ColumnType.DATETIME:
        return ColumnSemanticRole.TIME

    if dtype == ColumnType.NUMERIC:
        return ColumnSemanticRole.METRIC

    if dtype == ColumnType.BOOLEAN:
        return ColumnSemanticRole.DIMENSION

    if dtype in (ColumnType.CATEGORICAL, ColumnType.TEXT):
        is_entity_like = any(
            keyword in lowered_name
            for keyword in active_rules.entity_keywords
        )
        if (
            is_entity_like
            and unique_ratio >= active_rules.entity_unique_ratio
        ):
            return ColumnSemanticRole.ENTITY
        return ColumnSemanticRole.DIMENSION

    return ColumnSemanticRole.DIMENSION
