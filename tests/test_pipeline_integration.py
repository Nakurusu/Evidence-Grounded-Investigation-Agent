"""End-to-end integration tests for the full investigation pipeline.

These tests exercise the pipeline from CSV parsing through to the
AIInvestigationReport, verifying that every stage produces valid output
and that the stage outputs are compatible with each other.
"""

import json
from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.services.parser import parse_file
from app.services.normalizer import normalize_dataframe
from app.services.validator import validate_dataframe
from app.services.profiler import profile_dataframe
from app.services.quality import assess_data_quality
from app.services.signal_detector import detect_signals
from app.services.question_generator import generate_questions
from app.services.hypothesis_generator import generate_hypotheses
from app.services.evidence import generate_all_evidence
from app.services.hypothesis_validator import validate_hypotheses
from app.services.analyzer import analyze_dataframe
from app.services.report_generator import generate_report
from app.services.narrative_generator import MockNarrativeGenerator
from app.services.interactive_investigator import InteractiveInvestigator
from app.schemas.ai_report import AIInvestigationReport


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _make_csv(path: str, df: pd.DataFrame) -> str:
    import tempfile, os
    full = os.path.join(path, "test_temp.csv")
    df.to_csv(full, index=False)
    return full


# ═══════════════════════════════════════════════════════════════════════
# Full pipeline tests
# ═══════════════════════════════════════════════════════════════════════


class TestFullPipeline:
    """Exercise every pipeline stage with a realistic dataset."""

    def test_pipeline_runs_end_to_end(self, integration_df, tmp_path):
        path = _make_csv(str(tmp_path), integration_df)
        df = parse_file(path)
        df = normalize_dataframe(df)
        validate_dataframe(df)
        profile = profile_dataframe(df)
        quality = assess_data_quality(df)

        signals = detect_signals(df, profile)
        questions = generate_questions(signals)
        hypotheses = generate_hypotheses(signals)
        evidence = generate_all_evidence(df, profile, hypotheses, signals)
        validation = validate_hypotheses(hypotheses, evidence)
        summary = analyze_dataframe(df, profile)
        report = generate_report(validation, profile, summary)

        gen = MockNarrativeGenerator()
        narrative, metadata = gen.generate(report)

        investigator = InteractiveInvestigator()
        interactive = investigator.investigate(report)

        ai_report = AIInvestigationReport(
            investigation_report=report,
            narrative=narrative,
            model_metadata=metadata,
            interactive_investigation=interactive,
        )

        # Structural assertions
        assert len(report.findings) > 0
        assert len(narrative.key_findings) > 0
        assert len(interactive.follow_up_questions) > 0
        assert ai_report.model_metadata is not None

    def test_each_stage_output_usable_by_next(self, integration_df, tmp_path):
        """Verify stage outputs are valid inputs to the next stage."""
        path = _make_csv(str(tmp_path), integration_df)
        df = normalize_dataframe(parse_file(path))
        validate_dataframe(df)

        # Profile → Signals
        profile = profile_dataframe(df)
        signals = detect_signals(df, profile)
        assert signals is not None

        # Signals → Questions
        questions = generate_questions(signals)
        assert questions.questions  # at least some

        # Signals → Hypotheses
        hypotheses = generate_hypotheses(signals)
        assert len(hypotheses.hypotheses) > 0

        # Hypotheses + Signals → Evidence
        evidence = generate_all_evidence(df, profile, hypotheses, signals)
        assert len(evidence) == len(hypotheses.hypotheses)

        # Hypotheses + Evidence → Validation
        validation = validate_hypotheses(hypotheses, evidence)
        assert len(validation.validated) == len(hypotheses.hypotheses)

        # Validation + Profile → Report
        summary = analyze_dataframe(df, profile)
        report = generate_report(validation, profile, summary)
        assert len(report.findings) == len(validation.validated)

        # Report → Narrative
        gen = MockNarrativeGenerator()
        narrative, metadata = gen.generate(report)
        assert narrative.executive_summary

        # Report → Interactive
        investigator = InteractiveInvestigator()
        interactive = investigator.investigate(report)
        assert interactive is not None

    def test_pipeline_deterministic(self, integration_df, tmp_path):
        """Same input should produce structurally identical output."""
        def run():
            path = _make_csv(str(tmp_path), integration_df)
            df = normalize_dataframe(parse_file(path))
            validate_dataframe(df)
            profile = profile_dataframe(df)
            signals = detect_signals(df, profile)
            hypotheses = generate_hypotheses(signals)
            evidence = generate_all_evidence(df, profile, hypotheses, signals)
            validation = validate_hypotheses(hypotheses, evidence)
            summary = analyze_dataframe(df, profile)
            return generate_report(validation, profile, summary)

        report1 = run()
        report2 = run()

        assert report1.executive_summary.total_hypotheses == report2.executive_summary.total_hypotheses
        assert report1.executive_summary.overall_risk == report2.executive_summary.overall_risk
        assert len(report1.findings) == len(report2.findings)
        for f1, f2 in zip(report1.findings, report2.findings):
            assert f1.title == f2.title
            assert f1.status == f2.status

    def test_ai_report_json_serializable(self, integration_df, tmp_path):
        """The final AIInvestigationReport must be JSON-serializable."""
        path = _make_csv(str(tmp_path), integration_df)
        df = normalize_dataframe(parse_file(path))
        validate_dataframe(df)
        profile = profile_dataframe(df)
        signals = detect_signals(df, profile)
        hypotheses = generate_hypotheses(signals)
        evidence = generate_all_evidence(df, profile, hypotheses, signals)
        validation = validate_hypotheses(hypotheses, evidence)
        report = generate_report(validation, profile, analyze_dataframe(df, profile))

        gen = MockNarrativeGenerator()
        narrative, metadata = gen.generate(report)
        investigator = InteractiveInvestigator()
        interactive = investigator.investigate(report)

        ai_report = AIInvestigationReport(
            investigation_report=report,
            narrative=narrative,
            model_metadata=metadata,
            interactive_investigation=interactive,
        )

        d = ai_report.model_dump()
        json_str = json.dumps(d, indent=2, default=str)
        roundtripped = json.loads(json_str)
        assert roundtripped["model_metadata"]["provider"] == "mock"

    def test_empty_dataset_is_rejected_by_validator(self, empty_df, tmp_path):
        """An empty DataFrame should be rejected before the pipeline runs."""
        path = _make_csv(str(tmp_path), empty_df)
        df = normalize_dataframe(parse_file(path))

        with pytest.raises(ValueError, match="Dataset is empty"):
            validate_dataframe(df)
