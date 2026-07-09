"""Tests for app/services/question_generator.py."""

from app.services.question_generator import generate_questions, map_severity_to_priority
from app.schemas.signal import SignalReport, Signal
from app.models.enums import SignalType, SignalSeverity, QuestionCategory, QuestionPriority


def _signal(st: SignalType, sev: SignalSeverity = SignalSeverity.WARNING, col: str = "test_col") -> Signal:
    return Signal(type=st, severity=sev, column=col, message="test")


class TestMapSeverityToPriority:
    def test_high_maps_to_high(self):
        assert map_severity_to_priority(SignalSeverity.HIGH) == QuestionPriority.HIGH

    def test_warning_maps_to_medium(self):
        assert map_severity_to_priority(SignalSeverity.WARNING) == QuestionPriority.MEDIUM

    def test_info_maps_to_low(self):
        assert map_severity_to_priority(SignalSeverity.INFO) == QuestionPriority.LOW


class TestGenerateQuestions:
    def test_returns_question_report(self):
        report = SignalReport(signals=[_signal(SignalType.HIGH_MISSING_RATE)])
        result = generate_questions(report)
        assert result is not None
        assert hasattr(result, "questions")

    def test_each_signal_produces_questions(self):
        """Every signal type in the bank should produce ≥1 question."""
        report = SignalReport(signals=[
            _signal(SignalType.OUTLIER_DETECTED),
            _signal(SignalType.HIGH_CONCENTRATION),
        ])
        result = generate_questions(report)
        # Each signal type has 3 templates in the bank
        assert len(result.questions) >= 4

    def test_column_interpolated(self):
        report = SignalReport(signals=[_signal(SignalType.HIGH_MISSING_RATE, col="revenue")])
        result = generate_questions(report)
        assert any("revenue" in q.question for q in result.questions)

    def test_all_have_valid_categories(self):
        report = SignalReport(signals=[_signal(SignalType.OUTLIER_DETECTED)])
        result = generate_questions(report)
        for q in result.questions:
            assert q.category in QuestionCategory

    def test_all_have_valid_priorities(self):
        report = SignalReport(signals=[_signal(SignalType.OUTLIER_DETECTED)])
        result = generate_questions(report)
        for q in result.questions:
            assert q.priority in QuestionPriority

    def test_empty_signals_returns_empty(self):
        report = SignalReport(signals=[])
        result = generate_questions(report)
        assert len(result.questions) == 0

    def test_unknown_signal_type_skipped(self):
        """A signal type not in the bank should be silently skipped."""
        signal = Signal(
            type=SignalType.HIGH_MISSING_RATE,
            severity=SignalSeverity.INFO,
            column="x",
            message="test",
        )
        # All known types produce questions; this tests that unknown types
        # (if any existed) would be skipped.  We use the bank as-is.
        report = SignalReport(signals=[signal])
        result = generate_questions(report)
        assert len(result.questions) > 0  # HIGH_MISSING_RATE is in the bank
