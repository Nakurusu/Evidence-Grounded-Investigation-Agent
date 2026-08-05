from app.models.enums import SignalType, HypothesisStatus, HypothesisConfidence
from app.schemas.profile import DatasetProfile
from app.schemas.evidence import Evidence
from app.schemas.validated_hypothesis import (
    ValidatedHypothesis,
    ValidatedHypothesisReport,
)
from app.schemas.investigation_report import (
    InvestigationReport,
    ExecutiveSummary,
    DatasetSummary,
    Finding,
    QualitySummary,
)
from app.schemas.quality import DataQualityReport
from app.services.report_templates import _COMPOSITE_TEMPLATES, _FINDING_TEMPLATES


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _build_context(vh: ValidatedHypothesis) -> dict:
    ctx: dict = {}
    all_evidence = (
        vh.supporting_evidence + vh.contradicting_evidence + vh.neutral_evidence
    )
    for e in all_evidence:
        if e.metric and e.value is not None:
            try:
                ctx[e.metric] = float(e.value)
            except (ValueError, TypeError):
                ctx[e.metric] = e.value
        if e.related_column:
            ctx.setdefault("column", e.related_column)
    return ctx


def _format_template(template: str, ctx: dict) -> str:
    try:
        return template.format(**ctx)
    except (KeyError, ValueError):
        return template


# ---------------------------------------------------------------------------
# Finding builders
# ---------------------------------------------------------------------------

def _build_simple_finding(vh: ValidatedHypothesis) -> Finding:
    signal_type = vh.hypothesis.supporting_signals[0]
    status = vh.status
    ctx = _build_context(vh)

    templates = _FINDING_TEMPLATES.get(signal_type, {}).get(status)
    if templates is None:
        return Finding(
            title=vh.hypothesis.title,
            observation=f"{vh.hypothesis.description}",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="该发现暂无详细分析模板。",
            business_impact="无法自动评估业务影响。",
            recommendation="建议人工审查。",
        )

    return Finding(
        title=vh.hypothesis.title,
        observation=_format_template(templates["observation"], ctx),
        status=status,
        confidence=vh.adjusted_confidence,
        supporting_evidence=vh.supporting_evidence,
        contradicting_evidence=vh.contradicting_evidence,
        analysis=_format_template(templates["analysis"], ctx),
        business_impact=_format_template(templates["business_impact"], ctx),
        recommendation=_format_template(templates["recommendation"], ctx),
    )


def _build_composite_finding(vh: ValidatedHypothesis) -> Finding:
    signal_key = frozenset(vh.hypothesis.supporting_signals)
    status = vh.status
    ctx = _build_context(vh)

    composite = _COMPOSITE_TEMPLATES.get(signal_key, {}).get(status)
    if composite is None:
        return Finding(
            title=vh.hypothesis.title,
            observation=f"检测到组合信号模式：{', '.join(s.value for s in vh.hypothesis.supporting_signals)}。",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="该组合发现暂无详细分析模板。",
            business_impact="无法自动评估业务影响。",
            recommendation="建议对组合信号进行人工审查。",
        )

    return Finding(
        title=vh.hypothesis.title,
        observation=_format_template(composite["observation"], ctx),
        status=status,
        confidence=vh.adjusted_confidence,
        supporting_evidence=vh.supporting_evidence,
        contradicting_evidence=vh.contradicting_evidence,
        analysis=_format_template(composite["analysis"], ctx),
        business_impact=_format_template(composite["business_impact"], ctx),
        recommendation=_format_template(composite["recommendation"], ctx),
    )


def _extract_affected_columns(vh: ValidatedHypothesis) -> list[str]:
    columns = set(vh.hypothesis.related_columns)
    for evidence in (
        vh.supporting_evidence + vh.contradicting_evidence + vh.neutral_evidence
    ):
        if evidence.related_column:
            columns.add(evidence.related_column)
    return sorted(columns)


def _extract_key_metrics(
    vh: ValidatedHypothesis,
) -> dict[str, float | int | str]:
    metrics: dict[str, float | int | str] = {}
    for evidence in vh.supporting_evidence:
        if evidence.metric is None or evidence.value is None:
            continue
        value = evidence.value
        if isinstance(value, (int, float, str)):
            metrics[evidence.metric] = value
    return metrics


def _build_trace(vh: ValidatedHypothesis) -> dict[str, list[str] | str]:
    return {
        "signals": [signal.value for signal in vh.hypothesis.supporting_signals],
        "hypothesis": vh.hypothesis.title,
        "status": vh.status.value,
        "supporting_evidence": [e.title for e in vh.supporting_evidence],
        "contradicting_evidence": [e.title for e in vh.contradicting_evidence],
        "neutral_evidence": [e.title for e in vh.neutral_evidence],
    }


def _evidence_strength(vh: ValidatedHypothesis) -> str:
    if vh.status == HypothesisStatus.REFUTED:
        return "contradicted"
    if vh.status == HypothesisStatus.INCONCLUSIVE:
        return "limited"
    if (
        len(vh.supporting_evidence) >= 2
        and vh.adjusted_confidence == HypothesisConfidence.HIGH
    ):
        return "strong"
    if vh.supporting_evidence:
        return "moderate"
    return "limited"


def _uncertainty_notes(vh: ValidatedHypothesis) -> list[str]:
    notes: list[str] = []
    if vh.status == HypothesisStatus.INCONCLUSIVE:
        notes.append("当前证据不足以确认或否定该假设。")
    if vh.neutral_evidence:
        notes.append("部分证据未达到支持或反驳阈值，应谨慎解读。")
    if any(e.sample_size is not None and e.sample_size < 4 for e in (
        vh.supporting_evidence + vh.contradicting_evidence + vh.neutral_evidence
    )):
        notes.append("部分统计基于较少样本点，稳定性有限。")
    if any(
        signal in {
            SignalType.INCREASING_TREND,
            SignalType.DECREASING_TREND,
            SignalType.HIGH_CONCENTRATION,
        }
        for signal in vh.hypothesis.supporting_signals
    ):
        notes.append("该发现描述的是数据模式，不应直接解释为因果关系。")
    return notes


def _enrich_finding(finding: Finding, vh: ValidatedHypothesis) -> Finding:
    primary_signal_type = (
        vh.hypothesis.supporting_signals[0].value
        if vh.hypothesis.supporting_signals
        else None
    )
    return finding.model_copy(
        update={
            "primary_signal_type": primary_signal_type,
            "affected_columns": _extract_affected_columns(vh),
            "key_metrics": _extract_key_metrics(vh),
            "trace": _build_trace(vh),
            "evidence_strength": _evidence_strength(vh),
            "uncertainty_notes": _uncertainty_notes(vh),
        }
    )


_RISK_SIGNAL_TYPES = {
    SignalType.DECREASING_TREND,
    SignalType.HIGH_CONCENTRATION,
    SignalType.HIGH_MISSING_RATE,
    SignalType.OUTLIER_DETECTED,
}


def _score_overall_risk(validated: list[ValidatedHypothesis]) -> str:
    supported_risk = [
        vh for vh in validated
        if vh.status == HypothesisStatus.SUPPORTED
        and any(s in _RISK_SIGNAL_TYPES for s in vh.hypothesis.supporting_signals)
    ]
    high_confidence_risk = [
        vh for vh in supported_risk
        if vh.adjusted_confidence == HypothesisConfidence.HIGH
    ]

    if high_confidence_risk:
        return "high"
    if supported_risk:
        return "medium"
    return "low"


def _score_overall_confidence(validated: list[ValidatedHypothesis]) -> str:
    total = len(validated)
    if total == 0:
        return "low"

    resolved = [
        vh for vh in validated
        if vh.status in (HypothesisStatus.SUPPORTED, HypothesisStatus.REFUTED)
    ]
    inconclusive_ratio = 1 - (len(resolved) / total)
    high_confidence_resolved = [
        vh for vh in resolved
        if vh.adjusted_confidence == HypothesisConfidence.HIGH
    ]

    if inconclusive_ratio <= 0.2 and len(high_confidence_resolved) >= 1:
        return "high"
    if inconclusive_ratio <= 0.5 and resolved:
        return "medium"
    return "low"


def _build_finding(vh: ValidatedHypothesis) -> Finding:
    if vh.hypothesis.is_composite:
        return _enrich_finding(_build_composite_finding(vh), vh)
    return _enrich_finding(_build_simple_finding(vh), vh)


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------

def _build_executive_summary(
    validated: list[ValidatedHypothesis],
) -> ExecutiveSummary:
    supported = [vh for vh in validated if vh.status == HypothesisStatus.SUPPORTED]
    refuted = [vh for vh in validated if vh.status == HypothesisStatus.REFUTED]
    inconclusive = [vh for vh in validated if vh.status == HypothesisStatus.INCONCLUSIVE]

    high_priority = [
        vh.hypothesis.title
        for vh in supported
        if vh.adjusted_confidence == HypothesisConfidence.HIGH
    ][:3]

    total = len(validated)
    overall_risk = _score_overall_risk(validated)
    overall_confidence = _score_overall_confidence(validated)

    return ExecutiveSummary(
        total_hypotheses=total,
        supported_count=len(supported),
        refuted_count=len(refuted),
        inconclusive_count=len(inconclusive),
        highest_priority_findings=high_priority,
        overall_risk=overall_risk,
        overall_confidence=overall_confidence,
    )


# ---------------------------------------------------------------------------
# Dataset summary
# ---------------------------------------------------------------------------

def _build_dataset_summary(
    profile: DatasetProfile,
    analyzer_output: dict,
) -> DatasetSummary:
    return DatasetSummary(
        row_count=profile.row_count,
        column_count=profile.column_count,
        numeric_columns=analyzer_output.get("numeric_columns", []),
        categorical_columns=analyzer_output.get("categorical_columns", []),
        datetime_columns=analyzer_output.get("datetime_columns", []),
        text_columns=analyzer_output.get("text_columns", []),
        boolean_columns=analyzer_output.get("boolean_columns", []),
    )


def _build_quality_summary(
    quality_report: DataQualityReport | None,
) -> QualitySummary | None:
    if quality_report is None:
        return None

    warnings: list[str] = []
    if quality_report.missing_rate > 20:
        warnings.append(
            f"整体缺失率为 {quality_report.missing_rate:.1f}%，可能影响结论可靠性。"
        )
    if quality_report.duplicate_rate > 5:
        warnings.append(
            f"重复行比例为 {quality_report.duplicate_rate:.1f}%，建议检查重复记录。"
        )
    high_missing_columns = [
        c for c in quality_report.columns if c.missing_rate > 20
    ]
    if high_missing_columns:
        names = "、".join(c.column for c in high_missing_columns[:5])
        warnings.append(f"字段 {names} 存在较高缺失率。")

    risk_level = "low"
    if quality_report.missing_rate > 30 or quality_report.duplicate_rate > 20:
        risk_level = "high"
    elif warnings:
        risk_level = "medium"

    return QualitySummary(
        issue_count=len(warnings),
        risk_level=risk_level,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def generate_report(
    validation_report: ValidatedHypothesisReport,
    profile: DatasetProfile,
    dataset_summary: dict,
    quality_report: DataQualityReport | None = None,
) -> InvestigationReport:
    findings = [
        _build_finding(vh) for vh in validation_report.validated
    ]

    seen: set[str] = set()
    next_steps: list[str] = []
    for f in findings:
        if f.recommendation not in seen:
            seen.add(f.recommendation)
            next_steps.append(f.recommendation)

    return InvestigationReport(
        executive_summary=_build_executive_summary(
            validation_report.validated
        ),
        dataset_summary=_build_dataset_summary(profile, dataset_summary),
        findings=findings,
        next_steps=next_steps,
        quality_summary=_build_quality_summary(quality_report),
    )
