"""Deterministic ranking for cause candidates.

Cause candidates are not root-cause claims. They are prioritized explanations
that deserve follow-up validation based on already validated findings.
"""

from app.models.enums import HypothesisConfidence, HypothesisStatus
from app.schemas.investigation_report import (
    CauseCandidate,
    Finding,
    QualitySummary,
)
from app.services.question_context import score_finding_for_question


_CONFIDENCE_SCORE = {
    HypothesisConfidence.HIGH: 20.0,
    HypothesisConfidence.MEDIUM: 12.0,
    HypothesisConfidence.LOW: 4.0,
}


_EVIDENCE_STRENGTH_SCORE = {
    "strong": 16.0,
    "moderate": 9.0,
    "limited": 2.0,
    "contradicted": -12.0,
}


def _status_score(status: HypothesisStatus) -> float:
    if status == HypothesisStatus.SUPPORTED:
        return 24.0
    if status == HypothesisStatus.INCONCLUSIVE:
        return 6.0
    return -20.0


def _signal_count(finding: Finding) -> int:
    raw_signals = finding.trace.get("signals", [])
    if isinstance(raw_signals, list):
        return len(raw_signals)
    return 0


def _quality_penalty(quality_summary: QualitySummary | None) -> float:
    if quality_summary is None:
        return 0.0
    if quality_summary.risk_level == "high":
        return 16.0
    if quality_summary.risk_level == "medium":
        return 8.0
    return 0.0


def _candidate_score(
    finding: Finding,
    investigation_question: str | None,
    quality_summary: QualitySummary | None,
) -> float:
    score = 0.0
    score += _status_score(finding.status)
    score += _CONFIDENCE_SCORE.get(finding.confidence, 0.0)
    score += len(finding.supporting_evidence) * 6.0
    score += _EVIDENCE_STRENGTH_SCORE.get(finding.evidence_strength or "", 0.0)
    score += max(0, _signal_count(finding) - 1) * 8.0
    score += score_finding_for_question(finding, investigation_question) * 4.0
    score -= len(finding.contradicting_evidence) * 8.0
    score -= len(finding.uncertainty_notes) * 3.0
    score -= _quality_penalty(quality_summary)
    return round(score, 2)


def _candidate_title(finding: Finding) -> str:
    return f"可能解释：{finding.title}"


def _candidate_explanation(finding: Finding) -> str:
    return (
        f"该候选解释来自已验证发现“{finding.title}”。"
        f"{finding.observation} 这说明它值得优先验证，但当前仍是候选解释，"
        "不能直接视为确定因果。"
    )


def _limitations(
    finding: Finding,
    quality_summary: QualitySummary | None,
) -> list[str]:
    limitations = list(finding.uncertainty_notes)
    limitations.extend(e.description for e in finding.contradicting_evidence)
    if quality_summary and quality_summary.warnings:
        limitations.extend(quality_summary.warnings[:2])
    if not limitations:
        limitations.append("当前证据支持该模式，但仍需要后续分析验证业务原因。")
    return limitations[:4]


def _candidate_confidence(finding: Finding) -> HypothesisConfidence:
    if finding.status == HypothesisStatus.INCONCLUSIVE:
        return HypothesisConfidence.LOW
    return finding.confidence


def rank_cause_candidates(
    findings: list[Finding],
    investigation_question: str | None = None,
    quality_summary: QualitySummary | None = None,
    limit: int = 5,
) -> list[CauseCandidate]:
    candidates: list[CauseCandidate] = []

    for finding in findings:
        if finding.status == HypothesisStatus.REFUTED:
            continue

        score = _candidate_score(
            finding,
            investigation_question,
            quality_summary,
        )
        candidates.append(
            CauseCandidate(
                title=_candidate_title(finding),
                explanation=_candidate_explanation(finding),
                score=score,
                confidence=_candidate_confidence(finding),
                related_columns=finding.affected_columns,
                supporting_finding_titles=[finding.title],
                supporting_evidence_titles=[
                    evidence.title for evidence in finding.supporting_evidence
                ],
                limitations=_limitations(finding, quality_summary),
                next_validation_step=finding.recommendation,
            )
        )

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return candidates[:limit]
