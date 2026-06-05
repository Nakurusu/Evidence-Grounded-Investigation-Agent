from pandas import DataFrame
import pandas as pd
from app.schemas.profile import DatasetProfile, ColumnProfile
from app.models.enums import ColumnType

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


def profile_dataframe(df: DataFrame) -> DatasetProfile:
    row_count = len(df)
    column_count = len(df.columns)
    column_profiles = []
    for column in df.columns:
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
                dtype=infer_column_type(df[column]),
                is_identifier=detect_identifiers(column, df[column]),
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

def infer_column_type(series) -> ColumnType:
    if pd.api.types.is_bool_dtype(series):
        return ColumnType.BOOLEAN
    if pd.api.types.is_numeric_dtype(series):
        return ColumnType.NUMERIC
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnType.DATETIME
    series_non_null = series.dropna()

    if len(series_non_null) > 0:
        try:
            pd.to_datetime(series_non_null, errors="raise")
            return ColumnType.DATETIME
        except Exception:
            pass
            
    unique_ratio = unique_value_ratio(series)
    if unique_ratio < 0.5:
        return ColumnType.CATEGORICAL
    else:
        return ColumnType.TEXT
    
def unique_value_ratio(series) -> float:
    non_null = series.dropna()
    return non_null.nunique() / len(non_null) if len(non_null) > 0 else 0

def detect_identifiers(column_name, series) -> bool:
    unique_ratio = unique_value_ratio(series)
    return unique_ratio > 0.95 and any(keyword in column_name.lower() for keyword in IDENTIFIER_KEYWORDS)