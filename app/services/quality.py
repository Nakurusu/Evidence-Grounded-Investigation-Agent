from pandas import DataFrame

from app.schemas.quality import (
    DataQualityReport,
    ColumnQuality,
)


def assess_data_quality(df: DataFrame) -> DataQualityReport:

    row_count = len(df)
    column_count = len(df.columns)

    total_cells = row_count * column_count

    missing_cells = int(df.isna().sum().sum())

    missing_rate = (
        missing_cells / total_cells * 100
        if total_cells > 0
        else 0
    )

    duplicate_rows = int(df.duplicated().sum())

    duplicate_rate = (
        duplicate_rows / row_count * 100
        if row_count > 0
        else 0
    )

    column_reports = []

    for column in df.columns:

        column_missing = int(
            df[column].isna().sum()
        )

        column_missing_rate = (
            column_missing / row_count * 100
            if row_count > 0
            else 0
        )

        if column_missing_rate > 0:

            column_reports.append(
                ColumnQuality(
                    column=column,
                    missing_rate=column_missing_rate
                )
            )

    return DataQualityReport(
        missing_rate=missing_rate,
        duplicate_rate=duplicate_rate,
        columns=column_reports
    )