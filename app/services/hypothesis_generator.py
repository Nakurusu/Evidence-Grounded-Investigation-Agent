from app.models.enums import HypothesisConfidence
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.schemas.signal import Signal
from app.schemas.signal import SignalReport, SignalSeverity


from app.services.hypothesis_templates import (
    COMPOSITE_HYPOTHESES,
    HYPOTHESIS_TEMPLATES,
)

def _signal_group_key(signal: Signal) -> str:
    if signal.metric_column and signal.dimension_column:
        return f"{signal.dimension_column}:{signal.metric_column}"
    if signal.metric_column:
        return signal.metric_column
    return signal.column or signal.type.value


def _related_columns(signals: list[Signal]) -> list[str]:
    columns: set[str] = set()
    for signal in signals:
        if signal.column:
            columns.add(signal.column)
        if signal.metric_column:
            columns.add(signal.metric_column)
        if signal.dimension_column:
            columns.add(signal.dimension_column)
    return sorted(columns)


def generate_composite_hypotheses(signal_report: SignalReport) -> list[Hypothesis]:
    hypotheses = []
    grouped_signals: dict[str, list[Signal]] = {}
    for signal in signal_report.signals:
        grouped_signals.setdefault(_signal_group_key(signal), []).append(signal)

    for required_signals, title, description, confidence in COMPOSITE_HYPOTHESES:
        for signals in grouped_signals.values():
            signal_types = {signal.type for signal in signals}
            if not required_signals.issubset(signal_types):
                continue

            related = [
                signal for signal in signals if signal.type in required_signals
            ]
            hypotheses.append(
                Hypothesis(
                    title=title,
                    description=description,
                    confidence=confidence,
                    supporting_signals=list(required_signals),
                    is_composite=True,
                    related_columns=_related_columns(related),
                )
            )

    return hypotheses

def generate_hypotheses(signal_report: SignalReport) -> HypothesisReport:
    hypotheses = []

    for signal in signal_report.signals:
        template = HYPOTHESIS_TEMPLATES.get(signal.type)
        if not template:
            continue

        title, description = template
        title = title.format(column=signal.column)
        description = description.format(column=signal.column)

        # confidence 可以根据 signal.severity 映射
        if signal.severity == SignalSeverity.HIGH:
            confidence = HypothesisConfidence.HIGH
        elif signal.severity == SignalSeverity.WARNING:
            confidence = HypothesisConfidence.MEDIUM
        else:
            confidence = HypothesisConfidence.LOW

        hypotheses.append(
            Hypothesis(
                title=title,
                description=description,
                confidence=confidence,
                supporting_signals=[signal.type],
                    related_columns=_related_columns([signal]),
            )
        )

    hypotheses.extend(
        generate_composite_hypotheses(signal_report)
    )

    return HypothesisReport(hypotheses=hypotheses)
