from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable

import pandas as pd

from app.core.logger import logger
from app.db.database import SessionLocal
from app.models.enums import TaskStatus
from app.models.task import Task
from app.schemas.ai_report import AIInvestigationReport
from app.schemas.evidence import Evidence
from app.schemas.hypothesis import HypothesisReport
from app.schemas.investigation_report import InvestigationReport
from app.schemas.profile import DatasetProfile
from app.schemas.quality import DataQualityReport
from app.schemas.question import QuestionReport
from app.schemas.signal import SignalReport
from app.schemas.validated_hypothesis import ValidatedHypothesisReport
from app.services.analyzer import analyze_dataframe
from app.services.cross_dataset_analyzer import CrossDatasetAnalyzer
from app.services.evidence import generate_all_evidence
from app.services.hypothesis_generator import generate_hypotheses
from app.services.hypothesis_validator import validate_hypotheses
from app.services.interactive_investigator import InteractiveInvestigator
from app.services.narrative_generator import MockNarrativeGenerator, get_narrative_generator
from app.services.normalizer import normalize_dataframe
from app.services.parser import parse_file
from app.services.profiler import profile_dataframe
from app.services.quality import assess_data_quality
from app.services.question_generator import generate_questions
from app.services.report_generator import generate_report
from app.services.signal_detector import detect_signals
from app.services.validator import validate_dataframe


ProgressCallback = Callable[[str, list[str], int, str | None], None]


@dataclass
class PipelineOutputs:
    profile: DatasetProfile
    signal_report: SignalReport
    question_report: QuestionReport
    hypothesis_report: HypothesisReport
    evidence_by_hypothesis: list[list[Evidence]]
    validation_report: ValidatedHypothesisReport
    investigation_report: InvestigationReport
    ai_report: AIInvestigationReport


STAGE_DETAILS = {
    "parsing": "正在读取并解析上传文件",
    "profiling": "正在识别字段类型、缺失率和唯一值",
    "signals": "正在检测异常值、趋势、集中度和分布信号",
    "questions": "正在根据检测到的信号生成调查问题",
    "hypotheses": "正在把信号转化为可验证假设",
    "evidence": "正在为每个假设生成统计证据",
    "validation": "正在用证据验证或反驳假设",
    "report": "正在生成结构化调查报告",
    "narrative": "正在生成普通语言调查摘要",
    "interactive": "正在生成后续问题、数据缺口和调查路径",
    "secondary_profiling": "正在分析辅助数据集的结构和信号",
    "cross_dataset": "正在查找跨数据集关系和调查线索",
    "completed": "调查已完成",
}


STAGE_EXPLANATIONS = {
    "parsing": {
        "title": "解析文件",
        "goal": "读取上传文件，并转换为可分析的数据表。",
        "input": "CSV / Excel 文件",
        "output": "DataFrame",
        "reason": "后续画像、信号检测和证据生成都依赖结构化数据。",
    },
    "profiling": {
        "title": "数据画像",
        "goal": "识别字段类型、缺失率、唯一值和基础数据结构。",
        "input": "规范化后的数据表",
        "output": "DatasetProfile",
        "reason": "信号检测必须先知道每个字段适合哪类统计方法。",
    },
    "signals": {
        "title": "信号检测",
        "goal": "查找异常值、趋势、集中度、偏度、缺失率和低方差等模式。",
        "input": "DatasetProfile 和原始数据",
        "output": "SignalReport",
        "reason": "先发现值得调查的模式，再生成问题和假设。",
    },
    "questions": {
        "title": "调查问题",
        "goal": "把检测到的信号转化为下一步应追问的问题。",
        "input": "SignalReport",
        "output": "QuestionReport",
        "reason": "问题用于指导调查方向，而不是直接给出结论。",
    },
    "hypotheses": {
        "title": "假设生成",
        "goal": "把信号组合成可以被证据验证或反驳的假设。",
        "input": "SignalReport",
        "output": "HypothesisReport",
        "reason": "调查报告需要验证假设，而不是罗列孤立信号。",
    },
    "evidence": {
        "title": "证据收集",
        "goal": "为每个假设计算统计证据和关键指标。",
        "input": "HypothesisReport、SignalReport 和原始数据",
        "output": "Evidence",
        "reason": "结论必须先被证据支持或反驳。",
    },
    "validation": {
        "title": "假设验证",
        "goal": "根据证据判断假设是被支持、被驳回还是未确定。",
        "input": "HypothesisReport 和 Evidence",
        "output": "ValidatedHypothesisReport",
        "reason": "这一步决定哪些发现可以进入最终报告，以及置信度边界。",
    },
    "report": {
        "title": "结构化报告",
        "goal": "生成发现、业务影响、建议、关键指标和证据追溯。",
        "input": "ValidatedHypothesisReport 和 DatasetProfile",
        "output": "InvestigationReport",
        "reason": "报告是确定性事实源，后续叙事只能解释它，不能改写结论。",
    },
    "narrative": {
        "title": "普通语言叙事",
        "goal": "把结构化报告改写为普通用户更容易理解的摘要。",
        "input": "InvestigationReport",
        "output": "Narrative",
        "reason": "用户需要先理解发生了什么、为什么重要、下一步查什么。",
    },
    "interactive": {
        "title": "后续调查",
        "goal": "生成后续问题、数据缺口和可继续调查的路径。",
        "input": "InvestigationReport",
        "output": "InteractiveInvestigationReport",
        "reason": "调查不止给出答案，也应指出哪些问题需要继续验证。",
    },
    "secondary_profiling": {
        "title": "辅助数据画像",
        "goal": "分析辅助数据集的字段结构和信号。",
        "input": "辅助数据集",
        "output": "辅助 DatasetProfile 和 SignalReport",
        "reason": "跨数据集分析必须先理解每个数据集本身。",
    },
    "cross_dataset": {
        "title": "跨数据集分析",
        "goal": "查找共享维度、关系和跨数据集调查线索。",
        "input": "主报告、主数据画像和辅助数据画像",
        "output": "InvestigationGraph",
        "reason": "多数据集调查需要说明数据之间如何相互补充或限制。",
    },
    "completed": {
        "title": "调查完成",
        "goal": "整理最终结果并保存任务输出。",
        "input": "AIInvestigationReport",
        "output": "任务结果",
        "reason": "用户现在可以查看结构化发现、叙事和后续调查建议。",
    },
}


def _progress_payload(
    stage: str,
    completed_stages: list[str],
    percent: int,
    detail: str | None = None,
    failed_stage: str | None = None,
) -> dict:
    explanation = STAGE_EXPLANATIONS.get(stage, {})
    return {
        "current_stage": stage,
        "completed_stages": completed_stages,
        "percent": percent,
        "stage_detail": detail or STAGE_DETAILS.get(stage),
        "failed_stage": failed_stage,
        "stage_title": explanation.get("title"),
        "stage_goal": explanation.get("goal"),
        "stage_input": explanation.get("input"),
        "stage_output": explanation.get("output"),
        "stage_reason": explanation.get("reason"),
    }


def _update_task_progress(
    db,
    task: Task,
    stage: str,
    completed_stages: list[str],
    percent: int,
    detail: str | None = None,
    failed_stage: str | None = None,
) -> None:
    task.current_stage = stage
    task.progress = _progress_payload(
        stage=stage,
        completed_stages=completed_stages,
        percent=percent,
        detail=detail,
        failed_stage=failed_stage,
    )
    db.commit()


def _run_full_pipeline(
    df: pd.DataFrame,
    quality_report: DataQualityReport | None = None,
    on_stage: ProgressCallback | None = None,
) -> PipelineOutputs:
    def stage(
        name: str,
        completed: list[str],
        percent: int,
        detail: str | None = None,
    ) -> None:
        if on_stage is not None:
            on_stage(name, completed, percent, detail)

    stage("profiling", ["parsing"], 20, STAGE_DETAILS["profiling"])
    profile = profile_dataframe(df)

    stage("signals", ["parsing", "profiling"], 32, STAGE_DETAILS["signals"])
    signal_report = detect_signals(df, profile)

    stage(
        "questions",
        ["parsing", "profiling", "signals"],
        42,
        STAGE_DETAILS["questions"],
    )
    question_report = generate_questions(signal_report)

    stage(
        "hypotheses",
        ["parsing", "profiling", "signals", "questions"],
        52,
        STAGE_DETAILS["hypotheses"],
    )
    hypothesis_report = generate_hypotheses(signal_report)

    stage(
        "evidence",
        ["parsing", "profiling", "signals", "questions", "hypotheses"],
        64,
        STAGE_DETAILS["evidence"],
    )
    evidence_by_hypothesis = generate_all_evidence(
        df, profile, hypothesis_report, signal_report
    )

    stage(
        "validation",
        [
            "parsing",
            "profiling",
            "signals",
            "questions",
            "hypotheses",
            "evidence",
        ],
        74,
        STAGE_DETAILS["validation"],
    )
    validation_report = validate_hypotheses(
        hypothesis_report, evidence_by_hypothesis
    )

    stage(
        "report",
        [
            "parsing",
            "profiling",
            "signals",
            "questions",
            "hypotheses",
            "evidence",
            "validation",
        ],
        82,
        STAGE_DETAILS["report"],
    )
    summary = analyze_dataframe(df, profile)
    report = generate_report(validation_report, profile, summary, quality_report)

    stage(
        "narrative",
        [
            "parsing",
            "profiling",
            "signals",
            "questions",
            "hypotheses",
            "evidence",
            "validation",
            "report",
        ],
        90,
        STAGE_DETAILS["narrative"],
    )
    generator = get_narrative_generator()
    try:
        narrative, metadata = generator.generate(report)
    except Exception:
        logger.exception("narrative generation failed; falling back to mock")
        narrative, metadata = MockNarrativeGenerator().generate(report)
        metadata.provider = "mock_fallback"

    stage(
        "interactive",
        [
            "parsing",
            "profiling",
            "signals",
            "questions",
            "hypotheses",
            "evidence",
            "validation",
            "report",
            "narrative",
        ],
        96,
        STAGE_DETAILS["interactive"],
    )
    investigator = InteractiveInvestigator()
    interactive = investigator.investigate(report)

    ai_report = AIInvestigationReport(
        investigation_report=report,
        narrative=narrative,
        model_metadata=metadata,
        interactive_investigation=interactive,
    )

    return PipelineOutputs(
        profile=profile,
        signal_report=signal_report,
        question_report=question_report,
        hypothesis_report=hypothesis_report,
        evidence_by_hypothesis=evidence_by_hypothesis,
        validation_report=validation_report,
        investigation_report=report,
        ai_report=ai_report,
    )


def _run_light_pipeline(df: pd.DataFrame) -> tuple[DatasetProfile, SignalReport]:
    profile = profile_dataframe(df)
    signal_report = detect_signals(df, profile)
    return profile, signal_report


def process_uploaded_file(task_id, file):
    db = SessionLocal()
    task = db.get(Task, task_id)
    current_stage = "parsing"

    try:
        logger.info(f"processing task {task_id}")
        task.status = TaskStatus.PROCESSING.value
        _update_task_progress(
            db, task, "parsing", [], 5, STAGE_DETAILS["parsing"]
        )

        df = parse_file(file)
        logger.info(f"parsed file for task {task_id}")

        current_stage = "profiling"
        df = normalize_dataframe(df)
        validate_dataframe(df)
        quality_report = assess_data_quality(df)
        logger.info(quality_report.model_dump())

        def on_stage(
            stage: str,
            completed: list[str],
            percent: int,
            detail: str | None,
        ) -> None:
            nonlocal current_stage
            current_stage = stage
            _update_task_progress(db, task, stage, completed, percent, detail)

        outputs = _run_full_pipeline(
            df, quality_report=quality_report, on_stage=on_stage
        )
        logger.info(outputs.question_report.model_dump())

        logger.info(f"completed task {task_id}")
        task.status = TaskStatus.COMPLETED.value
        task.result = outputs.ai_report.model_dump(mode="json")
        task.finished_at = datetime.now(UTC)
        _update_task_progress(
            db,
            task,
            "completed",
            [
                "parsing",
                "profiling",
                "signals",
                "questions",
                "hypotheses",
                "evidence",
                "validation",
                "report",
                "narrative",
                "interactive",
            ],
            100,
            STAGE_DETAILS["completed"],
        )
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(f"task failed: {task_id}")
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        task.finished_at = datetime.now(UTC)
        task.current_stage = current_stage
        task.progress = _progress_payload(
            stage=current_stage,
            completed_stages=[],
            percent=0,
            detail=f"阶段 {current_stage} 失败：{e}",
            failed_stage=current_stage,
        )
        db.commit()
        db.close()


def process_multi_dataset_upload(
    task_id: str,
    primary_file: str,
    secondary_files: list[str],
):
    db = SessionLocal()
    task = db.get(Task, task_id)
    current_stage = "parsing"

    try:
        logger.info(f"processing multi-dataset task {task_id}")
        task.status = TaskStatus.PROCESSING.value
        _update_task_progress(
            db, task, "parsing", [], 5, "正在解析主数据集"
        )

        primary_df = normalize_dataframe(parse_file(primary_file))
        validate_dataframe(primary_df)
        primary_quality_report = assess_data_quality(primary_df)
        logger.info(primary_quality_report.model_dump())

        def on_primary_stage(
            stage: str,
            completed: list[str],
            percent: int,
            detail: str | None,
        ) -> None:
            nonlocal current_stage
            current_stage = stage
            _update_task_progress(db, task, stage, completed, percent, detail)

        outputs = _run_full_pipeline(
            primary_df,
            quality_report=primary_quality_report,
            on_stage=on_primary_stage,
        )

        secondary_profiles: list[DatasetProfile] = []
        secondary_signal_reports: list[SignalReport] = []
        secondary_names: list[str] = []

        current_stage = "secondary_profiling"
        if secondary_files:
            _update_task_progress(
                db,
                task,
                "secondary_profiling",
                [
                    "parsing",
                    "profiling",
                    "signals",
                    "questions",
                    "hypotheses",
                    "evidence",
                    "validation",
                    "report",
                    "narrative",
                    "interactive",
                ],
                97,
                STAGE_DETAILS["secondary_profiling"],
            )

        for sec_path in (secondary_files or []):
            sec_df = normalize_dataframe(parse_file(sec_path))
            validate_dataframe(sec_df)
            profile, signals = _run_light_pipeline(sec_df)
            secondary_profiles.append(profile)
            secondary_signal_reports.append(signals)
            fname = sec_path.split("/")[-1].split("_", 1)[-1]
            secondary_names.append(fname)
            logger.info(f"secondary dataset profiled: {fname}")

        if secondary_profiles:
            current_stage = "cross_dataset"
            _update_task_progress(
                db,
                task,
                "cross_dataset",
                [
                    "parsing",
                    "profiling",
                    "signals",
                    "questions",
                    "hypotheses",
                    "evidence",
                    "validation",
                    "report",
                    "narrative",
                    "interactive",
                    "secondary_profiling",
                ],
                99,
                STAGE_DETAILS["cross_dataset"],
            )
            analyzer = CrossDatasetAnalyzer()
            graph = analyzer.analyze(
                primary_report=outputs.investigation_report,
                primary_profile=outputs.profile,
                secondary_profiles=secondary_profiles,
                secondary_signals=secondary_signal_reports,
                secondary_filenames=secondary_names,
            )
            outputs.ai_report.investigation_graph = graph
            logger.info(
                f"cross-dataset analysis: {len(graph.relations)} relations, "
                f"{len(graph.shared_dimensions)} shared dimensions"
            )

        logger.info(f"completed multi-dataset task {task_id}")
        task.status = TaskStatus.COMPLETED.value
        task.result = outputs.ai_report.model_dump(mode="json")
        task.finished_at = datetime.now(UTC)
        _update_task_progress(
            db,
            task,
            "completed",
            [
                "parsing",
                "profiling",
                "signals",
                "questions",
                "hypotheses",
                "evidence",
                "validation",
                "report",
                "narrative",
                "interactive",
                "secondary_profiling",
                "cross_dataset",
            ],
            100,
            STAGE_DETAILS["completed"],
        )
        db.commit()
        db.close()

    except Exception as e:
        logger.exception(f"multi-dataset task failed: {task_id}")
        task.status = TaskStatus.FAILED.value
        task.error_message = str(e)
        task.finished_at = datetime.now(UTC)
        task.current_stage = current_stage
        task.progress = _progress_payload(
            stage=current_stage,
            completed_stages=[],
            percent=0,
            detail=f"阶段 {current_stage} 失败：{e}",
            failed_stage=current_stage,
        )
        db.commit()
        db.close()
