"""Tests for runnable follow-up drill-down analyses."""

import pandas as pd

from app.models.enums import HypothesisConfidence, HypothesisStatus, SignalType
from app.schemas.ai_report import AIInvestigationReport
from app.schemas.evidence import Evidence
from app.schemas.interactive import FollowUpQuestion, InteractiveInvestigationReport
from app.schemas.investigation_report import (
    DatasetSummary,
    ExecutiveSummary,
    Finding,
    InvestigationReport,
)
from app.services.drilldown import DrillDownService


def _finding(
    signal_type: SignalType,
    affected_columns: list[str],
    title: str = "Test finding",
) -> Finding:
    return Finding(
        title=title,
        observation="Observation",
        status=HypothesisStatus.SUPPORTED,
        confidence=HypothesisConfidence.HIGH,
        supporting_evidence=[
            Evidence(
                title="Evidence",
                description="Evidence",
                supporting_signal=signal_type,
                related_column=affected_columns[-1],
            )
        ],
        contradicting_evidence=[],
        analysis="Analysis",
        business_impact="Impact",
        recommendation="Recommendation",
        primary_signal_type=signal_type.value,
        affected_columns=affected_columns,
    )


def _ai_report(
    finding: Finding,
    question: FollowUpQuestion,
) -> AIInvestigationReport:
    report = InvestigationReport(
        executive_summary=ExecutiveSummary(
            total_hypotheses=1,
            supported_count=1,
            refuted_count=0,
            inconclusive_count=0,
            highest_priority_findings=[finding.title],
            overall_risk="medium",
            overall_confidence="high",
        ),
        dataset_summary=DatasetSummary(
            row_count=10,
            column_count=4,
            numeric_columns=["revenue"],
            categorical_columns=["region"],
            datetime_columns=["date"],
            text_columns=[],
            boolean_columns=[],
            metric_columns=["revenue"],
            dimension_columns=["region"],
            time_columns=["date"],
            entity_columns=[],
            identifier_columns=[],
        ),
        findings=[finding],
        next_steps=[],
    )
    return AIInvestigationReport(
        investigation_report=report,
        interactive_investigation=InteractiveInvestigationReport(
            follow_up_questions=[question],
            data_gaps=[],
            investigation_paths=[],
            unresolved_areas=[],
        ),
    )


def _question(finding: Finding) -> FollowUpQuestion:
    return FollowUpQuestion(
        question="运行 drill-down",
        priority="high",
        category="drill_down",
        related_finding_titles=[finding.title],
        required_data=[],
    )


def test_outlier_drilldown_returns_records():
    df = pd.DataFrame({"revenue": [100] * 20 + [1000, 1200]})
    finding = _finding(SignalType.OUTLIER_DETECTED, ["revenue"])
    report = _ai_report(finding, _question(finding))

    result = DrillDownService().run(df, report, 0)

    assert result.status == "completed"
    assert result.analysis_type == "tail_records"
    assert result.sample_records
    assert any(item.label == "selected_record_count" for item in result.evidence)
    assert report.interactive_investigation.drilldown_steps == []


def test_trend_drilldown_breaks_down_by_dimension():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]
            ),
            "region": ["A", "A", "B", "B"],
            "revenue": [100, 200, 100, 80],
        }
    )
    finding = _finding(SignalType.INCREASING_TREND, ["revenue"])
    report = _ai_report(finding, _question(finding))

    result = DrillDownService().run(df, report, 0)

    assert result.status == "completed"
    assert result.analysis_type == "trend_by_dimension"
    assert result.sample_records[0]["region"] == "A"


def test_missingness_drilldown_finds_concentrated_group():
    df = pd.DataFrame(
        {
            "region": ["A", "A", "A", "B", "B", "B"],
            "revenue": [None, None, 10, 10, 20, 30],
        }
    )
    finding = _finding(SignalType.HIGH_MISSING_RATE, ["revenue"])
    report = _ai_report(finding, _question(finding))

    result = DrillDownService().run(df, report, 0)

    assert result.status == "completed"
    assert result.analysis_type == "missingness_by_dimension"
    assert result.sample_records[0]["region"] == "A"


def test_non_drilldown_question_is_unsupported():
    finding = _finding(SignalType.OUTLIER_DETECTED, ["revenue"])
    question = FollowUpQuestion(
        question="需要外部数据吗？",
        priority="medium",
        category="data_gap",
        related_finding_titles=[finding.title],
        required_data=["外部数据"],
    )
    report = _ai_report(finding, question)

    result = DrillDownService().run(pd.DataFrame({"revenue": [1, 2, 3]}), report, 0)

    assert result.status == "unsupported"
    assert result.analysis_type == "unsupported"
