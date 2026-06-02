from app.models.enums import SignalType
from app.schemas.signal import SignalReport
from app.schemas.question import Question, QuestionReport
from app.models.enums import QuestionCategory, QuestionPriority, SignalSeverity

QUESTION_BANK = {
    SignalType.HIGH_MISSING_RATE: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 缺失率较高，哪些业务流程可能导致了这些数据缺失？",
        ),
        (
            QuestionCategory.VALIDATION,
            "这些缺失数据是否集中发生在特定时间段或业务环节？",
        ),
        (
            QuestionCategory.VALIDATION,
            "缺失数据会对后续分析结果产生多大影响？",
        ),
    ],
    SignalType.HIGH_CARDINALITY: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 的唯一值非常多，它是标识符字段，还是应该进一步归类聚合？",
        ),
        (
            QuestionCategory.VALIDATION,
            "该字段是否适合作为分析维度使用？",
        ),
        (
            QuestionCategory.VALIDATION,
            "是否存在重复编码或命名不一致的问题？",
        ),
    ],
    SignalType.OUTLIER_DETECTED: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 存在异常值，这些异常值是数据质量问题还是反映了真实业务事件？",
        ),
        (
            QuestionCategory.VALIDATION,
            "异常值是否集中发生在特定时间或对象上？",
        ),
        (
            QuestionCategory.VALIDATION,
            "剔除异常值后结论是否会发生明显变化？",
        ),
    ],
    SignalType.INCREASING_TREND: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 呈现增长趋势，哪些因素可能正在推动这一增长？",
        ),
        (
            QuestionCategory.VALIDATION,
            "增长主要来自客户增长、价格变化还是购买频次提升？",
        ),
        (
            QuestionCategory.VALIDATION,
            "这种增长趋势是否具有持续性？",
        ),
    ],
    SignalType.DECREASING_TREND: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 呈现下降趋势，哪些因素可能导致了这一变化？",
        ),
        (
            QuestionCategory.VALIDATION,
            "下降是短期波动还是长期趋势？",
        ),
        (
            QuestionCategory.VALIDATION,
            "是否存在客户流失、需求下降或竞争加剧等因素？",
        ),
    ],
    SignalType.HIGH_CONCENTRATION: [
        (
            QuestionCategory.OBSERVATION,
            "业务表现高度集中，是否过度依赖少数产品、客户或类别？",
        ),
        (
            QuestionCategory.VALIDATION,
            "这种集中度是长期存在还是近期形成的？",
        ),
        (
            QuestionCategory.VALIDATION,
            "如果头部对象表现下降，整体业务会受到多大影响？",
        ),
    ],
    SignalType.RIGHT_SKEWED: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 呈右偏分布，是否存在少数极端值对整体结果产生了较大影响？",
        ),
        (
            QuestionCategory.VALIDATION,
            "中位数是否比平均值更能代表真实情况？",
        ),
        (
            QuestionCategory.VALIDATION,
            "头部样本贡献了多大比例的结果？",
        ),
    ],
    SignalType.LEFT_SKEWED: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 呈左偏分布，异常偏小的数值是否对应特殊业务场景？",
        ),
        (
            QuestionCategory.VALIDATION,
            "这些极小值是否由异常事件导致？",
        ),
        (
            QuestionCategory.VALIDATION,
            "去除极小值后整体分布是否恢复正常？",
        ),
    ],
    SignalType.LOW_VARIANCE: [
        (
            QuestionCategory.OBSERVATION,
            "{column} 的波动很小，这个字段是否仍然具有分析价值？",
        ),
        (
            QuestionCategory.VALIDATION,
            "该字段是否已经趋于稳定或缺乏区分度？",
        ),
        (
            QuestionCategory.VALIDATION,
            "是否可以在后续分析中降低该字段权重？",
        ),
    ],
}

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