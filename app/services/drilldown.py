"""Runnable drill-down analyses for interactive follow-up questions.

Milestone 4 turns a limited set of follow-up questions into executable
investigation steps.  The service keeps analysis deterministic and appends the
result to the interactive layer without modifying the original report.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
from pandas import DataFrame

from app.models.enums import SignalType
from app.schemas.ai_report import AIInvestigationReport
from app.schemas.interactive import (
    DrillDownEvidence,
    DrillDownResult,
    FollowUpQuestion,
)
from app.schemas.investigation_report import Finding


class DrillDownService:
    """Execute supported follow-up questions against the original dataset."""

    def run(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        question_index: int,
    ) -> DrillDownResult:
        interactive = report.interactive_investigation
        if interactive is None:
            raise ValueError("No interactive investigation is available")
        if question_index < 0 or question_index >= len(interactive.follow_up_questions):
            raise IndexError("Follow-up question index is out of range")

        question = interactive.follow_up_questions[question_index]
        if question.category != "drill_down":
            return self._unsupported(
                question,
                "该问题需要补充数据或人工判断，当前不能直接运行 drill-down。",
            )

        finding = self._resolve_finding(report, question)
        if finding is None:
            return self._unsupported(
                question,
                "无法把该问题关联到原始报告中的具体 finding。",
            )

        signal_type = self._signal_type(finding.primary_signal_type)
        if signal_type in {
            SignalType.OUTLIER_DETECTED,
            SignalType.RIGHT_SKEWED,
            SignalType.LEFT_SKEWED,
        }:
            return self._analyze_tail_records(df, report, question, finding, signal_type)
        if signal_type in {
            SignalType.INCREASING_TREND,
            SignalType.DECREASING_TREND,
        }:
            return self._analyze_trend_by_dimension(df, report, question, finding)
        if signal_type == SignalType.HIGH_CONCENTRATION:
            return self._analyze_concentration(df, report, question, finding)
        if signal_type == SignalType.HIGH_MISSING_RATE:
            return self._analyze_missingness(df, report, question, finding)

        return self._unsupported(
            question,
            "该 signal type 的可运行 drill-down 尚未实现。",
        )

    # ------------------------------------------------------------------
    # Supported analyses
    # ------------------------------------------------------------------

    def _analyze_tail_records(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        question: FollowUpQuestion,
        finding: Finding,
        signal_type: SignalType | None,
    ) -> DrillDownResult:
        metric = self._metric_column(df, report, finding)
        if metric is None:
            return self._unsupported(question, "没有可用于尾部或异常值分析的数值字段。")

        values = pd.to_numeric(df[metric], errors="coerce")
        non_null = values.dropna()
        if non_null.empty:
            return self._unsupported(question, f"字段 {metric} 没有可分析的非空数值。")

        if signal_type == SignalType.LEFT_SKEWED:
            threshold = float(non_null.quantile(0.05))
            mask = values <= threshold
            direction = "低值尾部"
        elif signal_type == SignalType.RIGHT_SKEWED:
            threshold = float(non_null.quantile(0.95))
            mask = values >= threshold
            direction = "高值尾部"
        else:
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            lower = float(q1 - 1.5 * iqr)
            upper = float(q3 + 1.5 * iqr)
            mask = (values < lower) | (values > upper)
            threshold = f"< {lower:.4g} 或 > {upper:.4g}"
            direction = "IQR 异常值"

        selected = df.loc[mask].copy()
        selected_count = int(len(selected))
        selected_sum = float(pd.to_numeric(selected[metric], errors="coerce").sum())
        total_sum = float(non_null.sum())
        share = selected_sum / total_sum if total_sum else 0

        sort_ascending = signal_type == SignalType.LEFT_SKEWED
        sample = selected.assign(_metric_sort=values[mask]).sort_values(
            "_metric_sort",
            ascending=sort_ascending,
        ).drop(columns=["_metric_sort"]).head(10)

        summary = (
            f"{metric} 的 {direction} 覆盖 {selected_count} 条记录，"
            f"约占非空记录的 {selected_count / len(non_null):.1%}。"
            f"这些记录贡献了 {metric} 总和的 {share:.1%}。"
        )

        return self._result(
            question=question,
            status="completed",
            analysis_type="tail_records",
            summary=summary,
            related_columns=[metric],
            evidence=[
                DrillDownEvidence(
                    label="selected_record_count",
                    value=selected_count,
                    description="被 drill-down 选中的尾部或异常记录数量。",
                ),
                DrillDownEvidence(
                    label="selected_value_share",
                    value=round(share, 4),
                    description=f"选中记录贡献的 {metric} 总值占比。",
                ),
                DrillDownEvidence(
                    label="selection_threshold",
                    value=threshold,
                    description="用于选择记录的阈值。",
                ),
            ],
            sample_records=self._records(sample),
            limitations=[
                "该分析只说明记录贡献和分布特征，不证明这些记录是业务原因。",
                "异常值基于当前数据集统计阈值识别，仍需要业务背景确认。",
            ],
        )

    def _analyze_trend_by_dimension(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        question: FollowUpQuestion,
        finding: Finding,
    ) -> DrillDownResult:
        metric = self._metric_column(df, report, finding)
        time_col = self._time_column(df, report)
        dimension = self._dimension_column(df, report, finding)
        if metric is None or time_col is None or dimension is None:
            return self._unsupported(
                question,
                "趋势拆解需要同时具备数值指标、时间字段和可分组维度。",
            )

        work = df[[time_col, dimension, metric]].dropna(subset=[time_col, dimension])
        if work.empty:
            return self._unsupported(question, "没有足够的非空时间和维度数据。")

        work = work.copy()
        work[time_col] = pd.to_datetime(work[time_col], errors="coerce")
        work[metric] = pd.to_numeric(work[metric], errors="coerce")
        work = work.dropna(subset=[time_col, metric])
        if work.empty:
            return self._unsupported(question, "没有足够的数值时间序列数据。")

        rows = []
        for value, group in work.groupby(dimension):
            ordered = group.sort_values(time_col)
            first = float(ordered[metric].iloc[0])
            last = float(ordered[metric].iloc[-1])
            change = last - first
            growth = change / abs(first) if first else None
            rows.append(
                {
                    dimension: value,
                    "first_value": round(first, 4),
                    "last_value": round(last, 4),
                    "absolute_change": round(change, 4),
                    "growth_rate": round(growth, 4) if growth is not None else None,
                    "points": int(len(ordered)),
                }
            )

        rows = sorted(rows, key=lambda r: abs(r["absolute_change"]), reverse=True)
        top_rows = rows[:8]
        leading = top_rows[0] if top_rows else None
        if leading:
            summary = (
                f"按 {dimension} 拆解后，{leading[dimension]} 对 {metric} 的变化最明显，"
                f"从 {leading['first_value']} 变为 {leading['last_value']}，"
                f"绝对变化为 {leading['absolute_change']}。"
            )
        else:
            summary = f"按 {dimension} 拆解后，没有发现可排序的 {metric} 趋势变化。"

        return self._result(
            question=question,
            status="completed",
            analysis_type="trend_by_dimension",
            summary=summary,
            related_columns=[time_col, dimension, metric],
            evidence=[
                DrillDownEvidence(
                    label="dimension_count",
                    value=len(rows),
                    description=f"参与趋势拆解的 {dimension} 分组数量。",
                ),
                DrillDownEvidence(
                    label="top_absolute_change",
                    value=leading["absolute_change"] if leading else None,
                    description="变化幅度最大的分组的绝对变化。",
                ),
            ],
            sample_records=self._records(pd.DataFrame(top_rows)),
            limitations=[
                "当前拆解使用每个分组的首尾值，适合定位方向，不替代完整时间序列建模。",
                "分组变化可能受样本量、季节性或一次性事件影响。",
            ],
        )

    def _analyze_concentration(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        question: FollowUpQuestion,
        finding: Finding,
    ) -> DrillDownResult:
        metric = self._metric_column(df, report, finding)
        dimension = self._dimension_column(df, report, finding)
        if metric is None or dimension is None:
            return self._unsupported(question, "集中度分析需要数值指标和分类维度。")

        work = df[[dimension, metric]].copy()
        work[metric] = pd.to_numeric(work[metric], errors="coerce")
        grouped = (
            work.dropna(subset=[dimension, metric])
            .groupby(dimension)[metric]
            .agg(["sum", "count", "mean"])
            .reset_index()
            .sort_values("sum", ascending=False)
        )
        if grouped.empty:
            return self._unsupported(question, "没有足够的数据进行集中度拆解。")

        total = float(grouped["sum"].sum())
        top = grouped.iloc[0]
        top_share = float(top["sum"]) / total if total else 0
        rest_sum = total - float(top["sum"])
        top_label = top[dimension]
        summary = (
            f"{dimension} 中的头部类别 {top_label} 贡献了 {metric} 总值的 "
            f"{top_share:.1%}。其余类别合计贡献 {rest_sum:.4g}。"
        )

        records = grouped.head(10).rename(
            columns={"sum": "total", "count": "record_count", "mean": "average"}
        )

        return self._result(
            question=question,
            status="completed",
            analysis_type="top_category_vs_rest",
            summary=summary,
            related_columns=[dimension, metric],
            evidence=[
                DrillDownEvidence(
                    label="top_category",
                    value=str(top_label),
                    description="贡献最高的类别。",
                ),
                DrillDownEvidence(
                    label="top_category_share",
                    value=round(top_share, 4),
                    description=f"头部类别贡献的 {metric} 占比。",
                ),
                DrillDownEvidence(
                    label="category_count",
                    value=int(len(grouped)),
                    description="参与比较的类别数量。",
                ),
            ],
            sample_records=self._records(records),
            limitations=[
                "该分析衡量贡献集中度，不直接判断集中是否健康或有风险。",
                "需要业务稳定性、流失或合同数据才能进一步评估头部类别风险。",
            ],
        )

    def _analyze_missingness(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        question: FollowUpQuestion,
        finding: Finding,
    ) -> DrillDownResult:
        metric = self._metric_column(df, report, finding) or self._first_existing_column(
            df,
            finding.affected_columns,
        )
        dimension = self._dimension_column(df, report, finding)
        if metric is None or dimension is None:
            return self._unsupported(question, "缺失集中度分析需要目标字段和可分组维度。")

        work = df[[dimension, metric]].copy()
        grouped = (
            work.groupby(dimension, dropna=False)[metric]
            .agg(total_count="size", missing_count=lambda s: int(s.isna().sum()))
            .reset_index()
        )
        grouped["missing_rate"] = grouped["missing_count"] / grouped["total_count"]
        grouped = grouped.sort_values(
            ["missing_rate", "missing_count"],
            ascending=False,
        )
        top = grouped.iloc[0] if not grouped.empty else None
        if top is None:
            return self._unsupported(question, "没有足够的数据进行缺失集中度分析。")

        summary = (
            f"{metric} 的缺失在 {dimension}={top[dimension]} 中最集中，"
            f"该分组缺失率为 {top['missing_rate']:.1%}，"
            f"缺失 {int(top['missing_count'])} / {int(top['total_count'])} 条。"
        )

        return self._result(
            question=question,
            status="completed",
            analysis_type="missingness_by_dimension",
            summary=summary,
            related_columns=[dimension, metric],
            evidence=[
                DrillDownEvidence(
                    label="highest_missing_group",
                    value=str(top[dimension]),
                    description=f"{metric} 缺失率最高的 {dimension} 分组。",
                ),
                DrillDownEvidence(
                    label="highest_missing_rate",
                    value=round(float(top["missing_rate"]), 4),
                    description="最高分组缺失率。",
                ),
                DrillDownEvidence(
                    label="missing_group_count",
                    value=int(len(grouped)),
                    description="参与缺失集中度检查的分组数量。",
                ),
            ],
            sample_records=self._records(grouped.head(10)),
            limitations=[
                "缺失集中在某些分组只能说明缺失不是完全均匀分布。",
                "缺失原因仍需结合采集流程、系统日志或业务规则确认。",
            ],
        )

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def _resolve_finding(
        self,
        report: AIInvestigationReport,
        question: FollowUpQuestion,
    ) -> Finding | None:
        findings = report.investigation_report.findings
        related_titles = set(question.related_finding_titles)
        for finding in findings:
            if finding.title in related_titles:
                return finding
        for finding in findings:
            if any(column in question.question for column in finding.affected_columns):
                return finding
        return findings[0] if findings else None

    def _signal_type(self, value: str | None) -> SignalType | None:
        if value is None:
            return None
        try:
            return SignalType(value)
        except ValueError:
            return None

    def _metric_column(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        finding: Finding,
    ) -> str | None:
        candidates = []
        candidates.extend(finding.affected_columns)
        candidates.extend(report.investigation_report.dataset_summary.metric_columns)
        return self._first_numeric_column(df, candidates)

    def _dimension_column(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
        finding: Finding,
    ) -> str | None:
        candidates = []
        candidates.extend(
            [
                column
                for column in finding.affected_columns
                if column in df.columns
            ]
        )
        candidates.extend(report.investigation_report.dataset_summary.dimension_columns)
        candidates.extend(report.investigation_report.dataset_summary.entity_columns)
        metric = self._metric_column(df, report, finding)
        time_col = self._time_column(df, report)
        for column in candidates:
            if column in df.columns and column not in {metric, time_col}:
                return column
        return None

    def _time_column(
        self,
        df: DataFrame,
        report: AIInvestigationReport,
    ) -> str | None:
        return self._first_existing_column(
            df,
            report.investigation_report.dataset_summary.time_columns,
        )

    def _first_existing_column(
        self,
        df: DataFrame,
        candidates: list[str],
    ) -> str | None:
        for column in candidates:
            if column in df.columns:
                return column
        return None

    def _first_numeric_column(
        self,
        df: DataFrame,
        candidates: list[str],
    ) -> str | None:
        for column in candidates:
            if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
                return column
        return None

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    def _result(
        self,
        question: FollowUpQuestion,
        status: str,
        analysis_type: str,
        summary: str,
        related_columns: list[str] | None = None,
        evidence: list[DrillDownEvidence] | None = None,
        sample_records: list[dict[str, object | None]] | None = None,
        limitations: list[str] | None = None,
    ) -> DrillDownResult:
        return DrillDownResult(
            step_id=str(uuid4()),
            question=question.question,
            status=status,
            analysis_type=analysis_type,
            summary=summary,
            related_columns=related_columns or [],
            evidence=evidence or [],
            sample_records=sample_records or [],
            limitations=limitations or [],
            generated_at=datetime.now(timezone.utc),
        )

    def _unsupported(
        self,
        question: FollowUpQuestion,
        reason: str,
    ) -> DrillDownResult:
        return self._result(
            question=question,
            status="unsupported",
            analysis_type="unsupported",
            summary=reason,
            limitations=[reason],
        )

    def _records(self, df: DataFrame) -> list[dict[str, object | None]]:
        if df.empty:
            return []
        records = []
        for record in df.head(10).to_dict(orient="records"):
            records.append(
                {
                    str(key): self._json_safe_value(value)
                    for key, value in record.items()
                }
            )
        return records

    def _json_safe_value(self, value) -> object | None:
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if hasattr(value, "item"):
            return value.item()
        return value
