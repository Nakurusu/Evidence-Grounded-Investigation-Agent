"""Question-aware ranking helpers for investigation outputs.

The first MVP implementation intentionally uses transparent keyword and
column-name matching. It changes presentation order only; it does not create,
remove, or alter statistical conclusions.
"""

from app.schemas.investigation_report import Finding


_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "decreasing_trend": (
        "下降",
        "下滑",
        "降低",
        "减少",
        "decline",
        "decrease",
        "drop",
        "fall",
        "down",
    ),
    "increasing_trend": (
        "增长",
        "上升",
        "增加",
        "提升",
        "increase",
        "growth",
        "rise",
        "up",
    ),
    "outlier_detected": (
        "异常",
        "极端",
        "离群",
        "outlier",
        "anomaly",
        "abnormal",
        "extreme",
    ),
    "high_missing_rate": (
        "缺失",
        "空值",
        "missing",
        "null",
        "blank",
    ),
    "high_concentration": (
        "集中",
        "头部",
        "依赖",
        "concentration",
        "concentrated",
        "dominant",
        "dependency",
    ),
    "right_skewed": (
        "偏斜",
        "偏态",
        "长尾",
        "skew",
        "skewed",
        "long tail",
    ),
    "left_skewed": (
        "偏斜",
        "偏态",
        "skew",
        "skewed",
    ),
    "low_variance": (
        "波动",
        "稳定",
        "方差",
        "variance",
        "variation",
        "volatility",
        "stable",
    ),
    "high_cardinality": (
        "唯一",
        "分散",
        "类别过多",
        "unique",
        "cardinality",
        "distinct",
    ),
}


def _normalize(text: str | None) -> str:
    return (text or "").strip().lower()


def _text_contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def score_finding_for_question(
    finding: Finding,
    investigation_question: str | None,
) -> int:
    """Score how closely a finding relates to a user question.

    Scores are deliberately small and interpretable:
    - affected column mentioned in the question: +4
    - primary signal type keyword appears in the question: +3
    - finding title or observation shares wording with the question: +1
    """

    question = _normalize(investigation_question)
    if not question:
        return 0

    score = 0
    for column in finding.affected_columns:
        column_text = _normalize(column)
        if column_text and column_text in question:
            score += 4

    signal_type = finding.primary_signal_type
    if signal_type and _text_contains_any(
        question, _SIGNAL_KEYWORDS.get(signal_type, ())
    ):
        score += 3

    title = _normalize(finding.title)
    observation = _normalize(finding.observation)
    question_terms = [
        term
        for term in question.replace("，", " ").replace("？", " ").split()
        if len(term) >= 2
    ]
    if any(term in title or term in observation for term in question_terms):
        score += 1

    return score


def rank_findings_by_question(
    findings: list[Finding],
    investigation_question: str | None,
) -> list[Finding]:
    """Return findings with question-related items first.

    Python's stable sort preserves the original deterministic pipeline order
    for findings with equal relevance.
    """

    if not _normalize(investigation_question):
        return findings

    return sorted(
        findings,
        key=lambda finding: score_finding_for_question(
            finding, investigation_question
        ),
        reverse=True,
    )
