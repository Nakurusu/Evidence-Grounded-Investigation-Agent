"""Tests for deterministic cause candidate ranking."""

from app.models.enums import HypothesisConfidence, HypothesisStatus
from app.schemas.evidence import Evidence
from app.schemas.investigation_report import Finding
from app.models.enums import SignalType
from app.services.cause_ranker import rank_cause_candidates


def _evidence(title: str, signal_type: SignalType, column: str) -> Evidence:
    return Evidence(
        title=title,
        description=title,
        metric="metric",
        value=1,
        supporting_signal=signal_type,
        related_column=column,
    )


def _finding(
    title: str,
    signal_type: SignalType,
    status: HypothesisStatus = HypothesisStatus.SUPPORTED,
    confidence: HypothesisConfidence = HypothesisConfidence.MEDIUM,
    supporting_count: int = 1,
    column: str = "revenue",
) -> Finding:
    return Finding(
        title=title,
        observation=f"{title} observation",
        status=status,
        confidence=confidence,
        supporting_evidence=[
            _evidence(f"evidence {i}", signal_type, column)
            for i in range(supporting_count)
        ],
        contradicting_evidence=[],
        analysis="analysis",
        business_impact="impact",
        recommendation=f"Validate {title}",
        primary_signal_type=signal_type.value,
        affected_columns=[column],
        trace={
            "signals": [signal_type.value],
            "hypothesis": title,
            "status": status.value,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "neutral_evidence": [],
        },
        evidence_strength="moderate",
        uncertainty_notes=[],
    )


def test_rank_cause_candidates_returns_top_candidates():
    findings = [
        _finding("Low confidence", SignalType.RIGHT_SKEWED, confidence=HypothesisConfidence.LOW),
        _finding("High confidence", SignalType.DECREASING_TREND, confidence=HypothesisConfidence.HIGH),
    ]

    candidates = rank_cause_candidates(findings)

    assert len(candidates) == 2
    assert candidates[0].supporting_finding_titles == ["High confidence"]
    assert candidates[0].score >= candidates[1].score


def test_rank_cause_candidates_skips_refuted_findings():
    findings = [
        _finding("Refuted", SignalType.RIGHT_SKEWED, status=HypothesisStatus.REFUTED),
        _finding("Supported", SignalType.DECREASING_TREND),
    ]

    candidates = rank_cause_candidates(findings)

    assert len(candidates) == 1
    assert candidates[0].supporting_finding_titles == ["Supported"]


def test_investigation_question_boosts_related_candidate():
    unrelated = _finding(
        "Region concentration",
        SignalType.HIGH_CONCENTRATION,
        confidence=HypothesisConfidence.HIGH,
        supporting_count=2,
        column="region",
    )
    related = _finding(
        "Revenue decreasing",
        SignalType.DECREASING_TREND,
        confidence=HypothesisConfidence.MEDIUM,
        supporting_count=1,
    )

    candidates = rank_cause_candidates(
        [unrelated, related],
        investigation_question="为什么 revenue 下降？",
    )

    assert candidates[0].supporting_finding_titles == ["Revenue decreasing"]


def test_candidate_language_does_not_claim_causality():
    finding = _finding("Revenue decreasing", SignalType.DECREASING_TREND)

    candidate = rank_cause_candidates([finding])[0]

    assert candidate.title.startswith("可能解释")
    assert "不能直接视为确定因果" in candidate.explanation
    assert candidate.next_validation_step == "Validate Revenue decreasing"
