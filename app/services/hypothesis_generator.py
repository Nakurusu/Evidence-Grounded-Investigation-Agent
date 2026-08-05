from app.models.enums import SignalType, HypothesisConfidence
from app.schemas.hypothesis import Hypothesis, HypothesisReport
from app.schemas.signal import Signal
from app.schemas.signal import SignalReport, SignalSeverity


HYPOTHESIS_TEMPLATES = {
    SignalType.HIGH_CONCENTRATION: (
        "{column} 显示集中度风险",
        "{column} 主要由少数产品、客户或类别贡献，存在集中度风险。"
    ),
    SignalType.RIGHT_SKEWED: (
        "{column} 可能存在头部效应",
        "{column} 呈明显右偏分布，少量高值样本可能对整体结果产生较大影响。"
    ),
    SignalType.LOW_VARIANCE: (
        "{column} 可能缺乏分析价值",
        "{column} 波动很小，缺乏区分能力，可能不适合作为分析维度。"
    ),
    SignalType.INCREASING_TREND: (
        "{column} 存在持续增长驱动因素",
        "{column} 持续增长，可能受到需求提升、客户增长或运营改善驱动。"
    ),
    SignalType.DECREASING_TREND: (
        "{column} 可能受到负面因素影响",
        "{column} 持续下降，可能受到客户流失、需求下降或竞争加剧等因素影响。"
    ),
    SignalType.OUTLIER_DETECTED: (
        "{column} 存在异常值",
        "{column} 中存在异常数据，可能反映业务事件或数据质量问题，需要进一步验证。"
    ),
    SignalType.HIGH_MISSING_RATE: (
        "{column} 的缺失数据可能影响分析结论",
        "{column} 缺失率较高，可能影响分析结果，需要关注业务流程或数据收集环节。"
    ),
    SignalType.LEFT_SKEWED: (
        "{column} 中的极小值可能对应特殊业务场景",
        "{column} 左偏分布，少数极小值可能反映特殊业务事件或异常情况。"
    ),
    SignalType.HIGH_CARDINALITY: (
    "{column} 可能包含过多唯一值",
    "{column} 拥有大量唯一值，可能是标识符字段或需要进一步归类。"
    )
}

COMPOSITE_HYPOTHESES = [
    (
        {SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED},
        "业务可能高度依赖少数头部对象",
        "集中度风险与右偏分布同时出现，说明少数头部对象可能贡献了大部分结果。",
        HypothesisConfidence.HIGH,
    ),
    (
        {SignalType.HIGH_CONCENTRATION, SignalType.INCREASING_TREND},
        "增长可能由少数头部对象驱动",
        "业务增长与集中度风险同时出现，增长可能主要来自少数头部产品、客户或类别。",
        HypothesisConfidence.HIGH,
    ),
    (
        {SignalType.HIGH_CONCENTRATION, SignalType.DECREASING_TREND},
        "业务存在头部依赖风险",
        "业务表现下降且集中度较高，头部对象的波动可能对整体结果产生显著影响。",
        HypothesisConfidence.HIGH,
    ),
    (
        {SignalType.OUTLIER_DETECTED, SignalType.RIGHT_SKEWED},
        "极端值可能正在影响整体结论",
        "异常值与右偏分布同时存在，少数极端样本可能显著影响统计结果。",
        HypothesisConfidence.MEDIUM,
    ),
    (
        {SignalType.HIGH_MISSING_RATE, SignalType.OUTLIER_DETECTED},
        "数据质量问题可能影响分析可靠性",
        "高缺失率与异常值同时存在，分析结果可能受到数据质量问题影响。",
        HypothesisConfidence.HIGH,
    ),
]

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
