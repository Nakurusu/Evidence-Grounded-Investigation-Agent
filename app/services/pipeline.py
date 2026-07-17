from app.services.parser import parse_file
from app.services.normalizer import normalize_dataframe
from app.services.analyzer import analyze_dataframe
from app.services.validator import validate_dataframe
from datetime import datetime, UTC
from app.db.database import SessionLocal
from app.models.task import Task
from app.core.logger import logger
from app.models.enums import TaskStatus
from app.services.profiler import profile_dataframe
from app.services.quality import assess_data_quality
from app.services.signal_detector import detect_signals
from app.services.evidence import generate_all_evidence
from app.services.hypothesis_generator import generate_hypotheses
from app.services.question_generator import generate_questions
from app.services.hypothesis_validator import validate_hypotheses
from app.services.report_generator import generate_report
from app.services.narrative_generator import get_narrative_generator
from app.schemas.ai_report import AIInvestigationReport
from app.services.interactive_investigator import InteractiveInvestigator
from app.services.cross_dataset_analyzer import CrossDatasetAnalyzer
from app.schemas.cross_dataset import InvestigationGraph
import pandas as pd


def _run_full_pipeline(df: pd.DataFrame) -> tuple:
    """Run all pipeline stages on a single DataFrame.

    Returns (report, profile, signal_report, ai_report).
    """
    profile = profile_dataframe(df)
    signal_report = detect_signals(df, profile)
    hypothesis_report = generate_hypotheses(signal_report)
    evidence_by_hypothesis = generate_all_evidence(
        df, profile, hypothesis_report, signal_report
    )
    validation_report = validate_hypotheses(
        hypothesis_report, evidence_by_hypothesis
    )
    summary = analyze_dataframe(df, profile)
    report = generate_report(validation_report, profile, summary)
    generator = get_narrative_generator()
    narrative, metadata = generator.generate(report)
    investigator = InteractiveInvestigator()
    interactive = investigator.investigate(report)
    ai_report = AIInvestigationReport(
        investigation_report=report,
        narrative=narrative,
        model_metadata=metadata,
        interactive_investigation=interactive,
    )
    return report, profile, signal_report, ai_report


def _run_light_pipeline(df: pd.DataFrame) -> tuple:
    """Run only Profile + Signals on a DataFrame (for secondary datasets)."""
    profile = profile_dataframe(df)
    signal_report = detect_signals(df, profile)
    return profile, signal_report


def process_uploaded_file(task_id, file):

    db = SessionLocal()
    task = db.get(Task, task_id)

    try:
        logger.info(
            f"processing task {task_id}"
        )
        task.status = TaskStatus.PROCESSING.value
        df = parse_file(file)
        logger.info(
            f"parsed file for task {task_id}"
        )
        df = normalize_dataframe(df)
        validate_dataframe(df)

        quality_report = assess_data_quality(df)
        logger.info(quality_report.model_dump())

        question_report = generate_questions(
            detect_signals(df, profile_dataframe(df))
        )
        logger.info(question_report.model_dump())

        _, _, _, ai_report = _run_full_pipeline(df)

        logger.info(
            f"completed task {task_id}"
        )
        task.status = TaskStatus.COMPLETED.value
        task.result = ai_report.model_dump()
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(
            f"task failed: {task_id}"
        )
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()


def process_multi_dataset_upload(
    task_id: str,
    primary_file: str,
    secondary_files: list[str],
):
    """Process a primary dataset with optional secondary datasets (Phase 9).

    Runs the full pipeline on the primary file and light pipeline
    (Profile + Signals) on each secondary file.  Then cross-analyzes
    all datasets to produce an InvestigationGraph.
    """
    from app.services.file_manager import UPLOAD_DIR

    db = SessionLocal()
    task = db.get(Task, task_id)

    try:
        logger.info(f"processing multi-dataset task {task_id}")
        task.status = TaskStatus.PROCESSING.value

        # -- Primary: full pipeline -------------------------------------
        primary_df = normalize_dataframe(parse_file(primary_file))
        validate_dataframe(primary_df)
        primary_report, primary_profile, primary_signals, ai_report = (
            _run_full_pipeline(primary_df)
        )

        # -- Secondary: light pipeline ----------------------------------
        secondary_profiles: list = []
        secondary_signal_reports: list = []
        secondary_names: list = []

        for sec_path in (secondary_files or []):
            sec_df = normalize_dataframe(parse_file(sec_path))
            validate_dataframe(sec_df)
            profile, signals = _run_light_pipeline(sec_df)
            secondary_profiles.append(profile)
            secondary_signal_reports.append(signals)
            # Extract original filename from upload path
            fname = sec_path.split("/")[-1].split("_", 1)[-1]
            secondary_names.append(fname)
            logger.info(f"secondary dataset profiled: {fname}")

        # -- Cross-dataset analysis (Phase 9) ---------------------------
        if secondary_profiles:
            analyzer = CrossDatasetAnalyzer()
            graph = analyzer.analyze(
                primary_report=primary_report,
                primary_profile=primary_profile,
                secondary_profiles=secondary_profiles,
                secondary_signals=secondary_signal_reports,
                secondary_filenames=secondary_names,
            )
            ai_report.investigation_graph = graph
            logger.info(
                f"cross-dataset analysis: {len(graph.relations)} relations, "
                f"{len(graph.shared_dimensions)} shared dimensions"
            )

        logger.info(f"completed multi-dataset task {task_id}")
        task.status = TaskStatus.COMPLETED.value
        task.result = ai_report.model_dump()
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(f"multi-dataset task failed: {task_id}")
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        task.finished_at = datetime.now(UTC)
        db.commit()
        db.close()