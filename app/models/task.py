from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base
from app.models.enums import TaskStatus
from sqlalchemy import Text

class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True)
    status = Column(String, default=TaskStatus.PENDING.value)
    filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    result = Column(JSONB)
    error_message = Column(Text, nullable=True)