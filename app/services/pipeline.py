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

        profile = profile_dataframe(df)
        logger.info(profile.model_dump())

        quality_report = assess_data_quality(df)
        logger.info(quality_report.model_dump())

        signal_report = detect_signals(df, profile)
        logger.info(signal_report.model_dump())

        question_report = generate_questions(signal_report)
        logger.info(question_report.model_dump())

        hypothesis_report = generate_hypotheses(signal_report)
        logger.info(hypothesis_report.model_dump())

        evidence_by_hypothesis = generate_all_evidence(
            df, profile, hypothesis_report, signal_report
        )
        logger.info(
            f"evidence collected for {len(evidence_by_hypothesis)} hypotheses"
        )

        validation_report = validate_hypotheses(
            hypothesis_report, evidence_by_hypothesis
        )
        logger.info(validation_report.model_dump())

        summary = analyze_dataframe(df, profile)
        logger.info(
            f"completed task {task_id}"
        )
        task.status = TaskStatus.COMPLETED.value
        task.result = summary
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