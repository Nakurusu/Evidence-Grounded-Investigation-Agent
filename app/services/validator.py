from pandas import DataFrame


def validate_dataframe(df: DataFrame) -> None:
    if df.empty:
        raise ValueError("Dataset is empty")

    if len(df.columns) == 0:
        raise ValueError("Dataset has no columns")