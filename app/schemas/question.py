from pydantic import BaseModel
from typing import List
from app.models.enums import QuestionCategory, QuestionPriority

class Question(BaseModel):
    signal_type: str
    column: str | None = None
    category: QuestionCategory
    priority: QuestionPriority
    question: str

class QuestionReport(BaseModel):
    questions: List[Question]