from pydantic import BaseModel

class ColumnQuality(BaseModel):
    column: str
    missing_rate: float


class DataQualityReport(BaseModel):
    missing_rate: float
    duplicate_rate: float

    columns: list[ColumnQuality]