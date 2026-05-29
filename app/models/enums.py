from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ColumnType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"

class SignalType(str, Enum):
    HIGH_MISSING_RATE = "high_missing_rate"
    HIGH_CARDINALITY = "high_cardinality"
    OUTLIER_DETECTED = "outlier_detected"

class SignalSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"