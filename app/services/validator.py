REQUIRED_COLUMNS = [
    "product",
    "sales"
]

def validate_columns(df):

    missing_columns = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )