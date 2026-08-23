"""Cross-Dataset Analyzer — Phase 9.

Consumes the primary InvestigationReport and secondary dataset profiles +
signal reports, producing an InvestigationGraph of cross-dataset
relationships.

Architecture
------------
This service sits ABOVE the single-dataset pipeline.  It never touches
raw DataFrames or CSV files — it operates exclusively on structured
InvestigationReport, DatasetProfile, and SignalReport objects.

Detection rules (deterministic):
1. Shared dimensions  — same-named columns across datasets
2. Correlated trends  — both datasets trend in the same direction
3. Opposite trends    — datasets trend in opposite directions
4. Complementary signals — concentration in one + trend in the other

Design principles:
- Deterministic — no LLM calls
- Extensible — detection rules are independent methods, easy to add more
- Minimal — v1 supports 1 primary + N secondary datasets
"""

from app.schemas.investigation_report import InvestigationReport
from app.schemas.profile import DatasetProfile
from app.schemas.signal import SignalReport
from app.schemas.cross_dataset import (
    CrossDatasetRelation,
    InvestigationGraph,
)
from app.models.enums import SignalType, ColumnType


class CrossDatasetAnalyzer:
    """Analyze relationships between datasets."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        primary_report: InvestigationReport,
        primary_profile: DatasetProfile,
        secondary_profiles: list[DatasetProfile],
        secondary_signals: list[SignalReport],
        secondary_filenames: list[str],
    ) -> InvestigationGraph:
        """Analyze cross-dataset relationships.

        Args:
            primary_report: Full InvestigationReport from the primary dataset.
            primary_profile: DatasetProfile for the primary dataset.
            secondary_profiles: Profiles for each secondary dataset.
            secondary_signals: SignalReports for each secondary dataset.
            secondary_filenames: Original filenames for each secondary dataset.

        Returns:
            An InvestigationGraph with shared dimensions, relations, and
            cross-dataset hypotheses.
        """
        primary_columns = {c.name: c for c in primary_profile.columns}
        primary_signal_types = self._extract_signal_types(primary_report)

        all_shared_dims: set[str] = set()
        all_relations: list[CrossDatasetRelation] = []
        all_hypotheses: list[str] = []

        for sec_profile, sec_signals, sec_filename in zip(
            secondary_profiles, secondary_signals, secondary_filenames
        ):
            sec_columns = {c.name: c for c in sec_profile.columns}
            sec_signal_types = self._extract_signal_types_from_report(sec_signals)

            # 1. Shared dimensions
            shared = self._find_shared_dimensions(
                primary_columns, sec_columns
            )
            all_shared_dims.update(shared)

            if shared:
                dims = ", ".join(sorted(shared))
                all_relations.append(
                    CrossDatasetRelation(
                        type="shared_dimension",
                        description=(
                            f"两个数据集共享 {len(shared)} 个维度："
                            f"{dims}。可通过这些维度交叉验证各数据集中的发现。"
                        ),
                        primary_context=f"主数据集包含字段：{dims}",
                        secondary_context=(
                            f"辅助数据集 '{sec_filename}' "
                            f"包含字段：{dims}"
                        ),
                        shared_columns=sorted(shared),
                        confidence="high",
                    )
                )

            # 2. Correlated trends
            trend_relations = self._detect_trend_correlation(
                primary_signal_types, sec_signal_types,
                shared, sec_filename,
            )
            all_relations.extend(trend_relations)

            # 3. Complementary signals
            complementary = self._detect_complementary_signals(
                primary_signal_types, sec_signal_types,
                shared, sec_filename,
            )
            all_relations.extend(complementary)

            # 4. Generate hypotheses from relations
            hypotheses = self._generate_cross_hypotheses(
                all_relations, sec_filename
            )
            all_hypotheses.extend(hypotheses)

        # Deduplicate hypotheses
        all_hypotheses = list(dict.fromkeys(all_hypotheses))

        return InvestigationGraph(
            primary_dataset="primary",
            secondary_datasets=secondary_filenames,
            shared_dimensions=sorted(all_shared_dims),
            relations=all_relations,
            cross_hypotheses=all_hypotheses,
        )

    # ------------------------------------------------------------------
    # Detection rules
    # ------------------------------------------------------------------

    def _find_shared_dimensions(
        self,
        primary_cols: dict,
        secondary_cols: dict,
    ) -> set[str]:
        """Find columns that appear in both datasets with the same name."""
        shared_names = set(primary_cols.keys()) & set(secondary_cols.keys())
        return {
            name for name in shared_names
            if not primary_cols[name].is_identifier
            and not secondary_cols[name].is_identifier
        }

    def _detect_trend_correlation(
        self,
        primary_signals: set[SignalType],
        secondary_signals: set[SignalType],
        shared_dims: set[str],
        sec_filename: str,
    ) -> list[CrossDatasetRelation]:
        """Detect correlated or opposite trends between datasets."""
        relations: list[CrossDatasetRelation] = []

        has_primary_increase = SignalType.INCREASING_TREND in primary_signals
        has_primary_decrease = SignalType.DECREASING_TREND in primary_signals
        has_sec_increase = SignalType.INCREASING_TREND in secondary_signals
        has_sec_decrease = SignalType.DECREASING_TREND in secondary_signals

        # Correlated: both increasing or both decreasing
        if has_primary_increase and has_sec_increase:
            ctx = (
                f"共享维度：{', '.join(sorted(shared_dims))}"
                if shared_dims else "无共享维度"
            )
            relations.append(
                CrossDatasetRelation(
                    type="correlated_trend",
                    description=(
                        f"两个数据集均呈上升趋势。"
                        f"这可能表明存在共同的成长驱动力或关联业务流程（{ctx}）。"
                    ),
                    primary_context="主数据集呈上升趋势",
                    secondary_context=(
                        f"'{sec_filename}' 同样呈上升趋势"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="medium",
                )
            )

        if has_primary_decrease and has_sec_decrease:
            ctx = (
                f"共享维度：{', '.join(sorted(shared_dims))}"
                if shared_dims else "无共享维度"
            )
            relations.append(
                CrossDatasetRelation(
                    type="correlated_trend",
                    description=(
                        f"两个数据集均呈下降趋势。"
                        f"这可能表明存在共同的外部压力或系统性问题（{ctx}）。"
                    ),
                    primary_context="主数据集呈下降趋势",
                    secondary_context=(
                        f"'{sec_filename}' 同样呈下降趋势"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="medium",
                )
            )

        # Opposite: one increasing, one decreasing
        if has_primary_increase and has_sec_decrease:
            relations.append(
                CrossDatasetRelation(
                    type="opposite_trend",
                    description=(
                        f"主数据集呈上升趋势，而辅助数据集 '{sec_filename}' "
                        f"呈下降趋势。这种分歧可能表明存在替代效应，"
                        f"或两个数据集描述的是独立过程。"
                    ),
                    primary_context="主数据集呈上升趋势",
                    secondary_context=(
                        f"'{sec_filename}' 呈下降趋势"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="medium",
                )
            )

        if has_primary_decrease and has_sec_increase:
            relations.append(
                CrossDatasetRelation(
                    type="opposite_trend",
                    description=(
                        f"主数据集呈下降趋势，而辅助数据集 '{sec_filename}' "
                        f"呈上升趋势。这可能意味着资源或活动正从主数据集领域"
                        f"向辅助数据集领域转移。"
                    ),
                    primary_context="主数据集呈下降趋势",
                    secondary_context=(
                        f"'{sec_filename}' 呈上升趋势"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="medium",
                )
            )

        return relations

    def _detect_complementary_signals(
        self,
        primary_signals: set[SignalType],
        secondary_signals: set[SignalType],
        shared_dims: set[str],
        sec_filename: str,
    ) -> list[CrossDatasetRelation]:
        """Detect complementary patterns across datasets.

        E.g., primary has concentration risk, secondary has trend —
        together they tell a stronger story.
        """
        relations: list[CrossDatasetRelation] = []

        primary_has_conc = SignalType.HIGH_CONCENTRATION in primary_signals
        sec_has_trend = (
            SignalType.INCREASING_TREND in secondary_signals
            or SignalType.DECREASING_TREND in secondary_signals
        )

        if primary_has_conc and sec_has_trend:
            direction = (
                "上升" if SignalType.INCREASING_TREND in secondary_signals
                else "下降"
            )
            dim_ctx = (
                f"共享维度（{', '.join(sorted(shared_dims))}）"
                f"表明这些模式可能存在关联。"
                if shared_dims
                else "未发现共享维度——两者之间的关联可能是间接的。"
            )
            relations.append(
                CrossDatasetRelation(
                    type="complementary_signal",
                    description=(
                        f"主数据集的集中度风险与辅助数据集 '{sec_filename}' "
                        f"的{direction}趋势相结合，表明集中的对象可能"
                        f"受到辅助数据集趋势的影响。{dim_ctx}"
                    ),
                    primary_context="主数据集存在高集中度",
                    secondary_context=(
                        f"'{sec_filename}' 呈{direction}趋势"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="high" if shared_dims else "medium",
                )
            )

        return relations

    # ------------------------------------------------------------------
    # Hypothesis generation
    # ------------------------------------------------------------------

    def _generate_cross_hypotheses(
        self,
        relations: list[CrossDatasetRelation],
        sec_filename: str,
    ) -> list[str]:
        """Generate natural-language hypotheses from detected relations."""
        hypotheses: list[str] = []

        for r in relations:
            if r.type == "shared_dimension" and r.shared_columns:
                cols = ", ".join(r.shared_columns)
                hypotheses.append(
                    f"主数据集与 '{sec_filename}' 共享维度（{cols}）。"
                    f"通过这些维度交叉比对，可能揭示各数据集中"
                    f"所观察到的模式之间的因果关系。"
                )

            if r.type == "correlated_trend":
                hypotheses.append(
                    f"主数据集与 '{sec_filename}' 的趋势方向一致，"
                    f"可能存在共同的底层驱动因素。"
                    f"建议调查是否有同一外部因素（市场环境、季节性、政策变化）"
                    f"同时解释两个趋势。"
                )

            if r.type == "opposite_trend":
                hypotheses.append(
                    f"主数据集与 '{sec_filename}' 的趋势方向相反，"
                    f"可能存在因果关系或资源转移。"
                    f"建议调查活动从一个领域向另一个领域的转移"
                    f"是否解释了这种分歧。"
                )

            if r.type == "complementary_signal":
                hypotheses.append(
                    f"主数据集的集中度风险可能被 '{sec_filename}' 的趋势"
                    f"放大或缓解。建议按辅助数据集的维度对集中对象进行拆分，"
                    f"以理解两者之间的交互作用。"
                )

        return hypotheses

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_signal_types(report: InvestigationReport) -> set[SignalType]:
        """Extract the set of SignalTypes present in a report's findings."""
        types: set[SignalType] = set()
        for f in report.findings:
            for e in f.supporting_evidence:
                if e.supporting_signal is not None:
                    types.add(e.supporting_signal)
            for e in f.contradicting_evidence:
                if e.supporting_signal is not None:
                    types.add(e.supporting_signal)
        return types

    @staticmethod
    def _extract_signal_types_from_report(
        signal_report: SignalReport,
    ) -> set[SignalType]:
        """Extract SignalTypes from a SignalReport."""
        return {s.type for s in signal_report.signals}
