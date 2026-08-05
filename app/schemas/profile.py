from pydantic import BaseModel
from app.models.enums import ColumnSemanticRole, ColumnType

class ColumnProfile(BaseModel):
    name: str
    dtype: ColumnType   
    semantic_role: ColumnSemanticRole
    is_identifier: bool

    null_count: int
    null_percentage: float

    unique_count: int


class DatasetProfile(BaseModel):
    row_count: int
    column_count: int

    columns: list[ColumnProfile]
