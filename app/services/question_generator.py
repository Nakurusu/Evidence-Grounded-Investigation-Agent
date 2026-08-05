from app.schemas.signal import SignalReport
from app.schemas.question import Question, QuestionReport
from app.models.enums import QuestionPriority, SignalSeverity

from app.services.question_templates import QUESTION_BANK

def map_severity_to_priority(severity: SignalSeverity) -> QuestionPriority:
    if severity == SignalSeverity.HIGH:
        return QuestionPriority.HIGH
    elif severity == SignalSeverity.WARNING:
        return QuestionPriority.MEDIUM
    else:
        return QuestionPriority.LOW


def generate_questions(signal_report: SignalReport) -> QuestionReport:
    questions = []

    for signal in signal_report.signals:
        templates = QUESTION_BANK.get(signal.type)
        if not templates:
            continue
        for category, template in templates:
            questions.append(
                Question(
                    signal_type=signal.type,
                    column=signal.column,
                    category=category,
                    priority=map_severity_to_priority(signal.severity),
                    question=template.format(column=signal.column),
                )
            )

    return QuestionReport(questions=questions)
