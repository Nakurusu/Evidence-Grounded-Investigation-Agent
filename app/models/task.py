from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from db.database import Base

class Task(Base):

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True)

    status = Column(String, nullable=False)

    filename = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)

    finished_at = Column(DateTime(timezone=True))

    result = Column(JSONB)

    error = Column(Text)