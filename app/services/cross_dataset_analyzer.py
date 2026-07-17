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
                            f"Both datasets share {len(shared)} dimension(s): "
                            f"{dims}.  These can be used to cross-reference "
                            f"findings between datasets."
                        ),
                        primary_context=f"Primary dataset has columns: {dims}",
                        secondary_context=(
                            f"Secondary dataset '{sec_filename}' "
                            f"has columns: {dims}"
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
                f"shared dimensions: {', '.join(sorted(shared_dims))}"
                if shared_dims else "no shared dimensions"
            )
            relations.append(
                CrossDatasetRelation(
                    type="correlated_trend",
                    description=(
                        f"Both datasets show increasing trends.  "
                        f"This suggests a shared growth driver or related "
                        f"business processes ({ctx})."
                    ),
                    primary_context="Primary dataset has an increasing trend",
                    secondary_context=(
                        f"'{sec_filename}' also has an increasing trend"
                    ),
                    shared_columns=sorted(shared_dims),
                    confidence="medium",
                )
            )

        if has_primary_decrease and has_sec_decrease:
            ctx = (
                f"shared dimensions: {', '.join(sorted(shared_dims))}"
                if shared_dims else "no shared dimensions"
            )
            relations.append(
                CrossDatasetRelation(
                    type="correlated_trend",
                    description=(
                        f"Both datasets show decreasing trends.  "
                        f"This may indicate a shared external pressure or "
                        f"systemic issue ({ctx})."
                    ),
                    primary_context="Primary dataset has a decreasing trend",
                    secondary_context=(
                        f"'{sec_filename}' also has a decreasing trend"
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
                        "Primary dataset is increasing while secondary "
                        f"'{sec_filename}' is decreasing.  This divergence "
                        "may indicate a substitution effect or that the "
                        "datasets describe independent processes."
                    ),
                    primary_context="Primary dataset has an increasing trend",
                    secondary_context=(
                        f"'{sec_filename}' has a decreasing trend"
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
                        "Primary dataset is decreasing while secondary "
                        f"'{sec_filename}' is increasing.  This may indicate "
                        "a shift — resources or activity moving from the "
                        "primary domain to the secondary domain."
                    ),
                    primary_context="Primary dataset has a decreasing trend",
                    secondary_context=(
                        f"'{sec_filename}' has an increasing trend"
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
                "increasing" if SignalType.INCREASING_TREND in secondary_signals
                else "decreasing"
            )
            dim_ctx = (
                f"Shared dimensions ({', '.join(sorted(shared_dims))}) "
                f"suggest these patterns may be connected."
                if shared_dims
                else "No shared dimensions were found — the connection "
                     "may be indirect."
            )
            relations.append(
                CrossDatasetRelation(
                    type="complementary_signal",
                    description=(
                        f"Concentration risk in the primary dataset combined "
                        f"with a {direction} trend in '{sec_filename}' "
                        f"suggests the concentrated entities may be affected "
                        f"by the secondary dataset's trend.  {dim_ctx}"
                    ),
                    primary_context="Primary dataset has high concentration",
                    secondary_context=(
                        f"'{sec_filename}' has a {direction} trend"
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
                    f"The primary dataset and '{sec_filename}' share "
                    f"dimensions ({cols}).  Cross-referencing by these "
                    f"dimensions may reveal causal relationships between "
                    f"the patterns observed in each dataset."
                )

            if r.type == "correlated_trend":
                hypotheses.append(
                    f"The aligned trends between the primary dataset and "
                    f"'{sec_filename}' suggest a common underlying driver.  "
                    f"Investigate whether the same external factor (market "
                    f"conditions, seasonality, policy change) explains both trends."
                )

            if r.type == "opposite_trend":
                hypotheses.append(
                    f"The opposing trends between the primary dataset and "
                    f"'{sec_filename}' may indicate a causal relationship "
                    f"or resource shift.  Investigate whether activity "
                    f"moving from one domain to the other explains the "
                    f"divergence."
                )

            if r.type == "complementary_signal":
                hypotheses.append(
                    f"Concentration risk in the primary dataset may be "
                    f"amplified or mitigated by the trend in '{sec_filename}'.  "
                    f"Segment the concentrated entities by the secondary "
                    f"dataset's dimension to understand the interaction."
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
