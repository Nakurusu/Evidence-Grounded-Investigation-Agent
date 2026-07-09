"""Interactive investigation engine — Phase 8.

Consumes the deterministic InvestigationReport and produces a forward-looking
InteractiveInvestigationReport: follow-up questions, data gaps, guided
investigation paths, and unresolved areas.

Architecture
------------
This module sits at the END of the pipeline, after report generation and
narrative generation.  It answers the question: "What should I investigate
next?"

Like the question generator (Phase 4), it uses template-driven logic rather
than LLM calls.  This keeps the output deterministic and explainable.
Future phases may add an LLM-powered variant behind a shared interface.

Design principles:
- Every follow-up question links back to a finding in the report.
- Data gaps describe data the analyst DOES NOT HAVE — distinct from
  missing values IN the existing dataset.
- Investigation paths are step-by-step and executable without further
  guidance.
"""

from app.models.enums import SignalType, HypothesisStatus
from app.schemas.investigation_report import InvestigationReport, Finding
from app.schemas.interactive import (
    FollowUpQuestion,
    DataGap,
    InvestigationPath,
    InteractiveInvestigationReport,
)


# ---------------------------------------------------------------------------
# Follow-up question templates — one entry per SignalType
#
# Each entry maps a finding STATUS to one or more follow-up questions with
# category and required-data hints.
# ---------------------------------------------------------------------------

_DRILL_DOWN_TEMPLATES: dict[SignalType, list[dict]] = {
    SignalType.RIGHT_SKEWED: [
        {
            "question": (
                "Which specific records or segments are pulling the "
                "average above the median in '{column}'?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "Is the right skew in '{column}' consistent over time, "
                "or does it vary by period?"
            ),
            "category": "drill_down",
            "required_data": ["time-series breakdown of {column}"],
        },
        {
            "question": (
                "What percentage of total '{column}' value is contributed "
                "by the top 5% of records?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.LEFT_SKEWED: [
        {
            "question": (
                "Which specific records or segments are pulling the "
                "average below the median in '{column}'?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "Do the low-value records in '{column}' represent data "
                "errors, special cases, or systematic underperformance?"
            ),
            "category": "drill_down",
            "required_data": ["operational metadata for {column}"],
        },
    ],
    SignalType.OUTLIER_DETECTED: [
        {
            "question": (
                "Do the outliers in '{column}' correlate with specific "
                "categories, regions, or time periods?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "Are the outliers in '{column}' data entry errors, or "
                "do they represent legitimate business events?"
            ),
            "category": "drill_down",
            "required_data": [
                "transaction-level detail or audit logs for {column}"
            ],
        },
        {
            "question": (
                "How do key metrics change when outliers in '{column}' "
                "are excluded — are conclusions materially different?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.HIGH_CONCENTRATION: [
        {
            "question": (
                "Who are the top contributors in '{column}' and what is "
                "their retention risk?"
            ),
            "category": "drill_down",
            "required_data": [
                "entity-level profiles for top values in {column}",
                "historical retention/churn data",
            ],
        },
        {
            "question": (
                "Has the concentration in '{column}' been increasing or "
                "decreasing over time?"
            ),
            "category": "drill_down",
            "required_data": ["time-series of concentration metric"],
        },
        {
            "question": (
                "Is the concentration in '{column}' structural "
                "(consistent across all segments) or driven by one "
                "specific segment?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.INCREASING_TREND: [
        {
            "question": (
                "Is the growth in '{column}' broad-based or concentrated "
                "in a small number of segments?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "What is driving the growth in '{column}' — new customers, "
                "higher prices, or increased volume per customer?"
            ),
            "category": "drill_down",
            "required_data": [
                "customer-level transaction data",
                "pricing history",
            ],
        },
        {
            "question": (
                "Is the growth rate in '{column}' accelerating, stable, "
                "or decelerating?"
            ),
            "category": "drill_down",
            "required_data": ["longer time-series for {column}"],
        },
    ],
    SignalType.DECREASING_TREND: [
        {
            "question": (
                "Is the decline in '{column}' broad-based or concentrated "
                "in specific segments, products, or regions?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "Is the decline in '{column}' a recent development or "
                "part of a longer-term trend?"
            ),
            "category": "drill_down",
            "required_data": ["longer time-series for {column}"],
        },
        {
            "question": (
                "Have any external events (market changes, competitive "
                "actions, policy shifts) coincided with the decline in "
                "'{column}'?"
            ),
            "category": "data_gap",
            "required_data": [
                "external market data",
                "competitive intelligence",
            ],
        },
    ],
    SignalType.HIGH_MISSING_RATE: [
        {
            "question": (
                "Is the missing data in '{column}' random or systematic "
                "(e.g., concentrated in specific time periods, regions, "
                "or categories)?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "What process or system gap is causing the missing data "
                "in '{column}'?"
            ),
            "category": "data_gap",
            "required_data": [
                "data collection process documentation",
                "system logs",
            ],
        },
    ],
    SignalType.HIGH_CARDINALITY: [
        {
            "question": (
                "Can '{column}' be aggregated into fewer, more meaningful "
                "categories for analysis?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": (
                "Does '{column}' contain duplicate or near-duplicate "
                "values that should be consolidated?"
            ),
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.LOW_VARIANCE: [
        {
            "question": (
                "Is the low variance in '{column}' expected (e.g., a "
                "fixed-price product) or does it indicate a data quality "
                "issue (e.g., default values, capped measurements)?"
            ),
            "category": "drill_down",
            "required_data": ["business context for {column}"],
        },
        {
            "question": (
                "Are there related metrics with higher variance that "
                "could serve as better analytical dimensions than "
                "'{column}'?"
            ),
            "category": "drill_down",
            "required_data": ["additional related metrics"],
        },
    ],
}

# ---------------------------------------------------------------------------
# Data gap recommendations — what data the analyst should seek
# ---------------------------------------------------------------------------

_DATA_GAP_TEMPLATES: dict[SignalType, list[dict]] = {
    SignalType.HIGH_CONCENTRATION: [
        {
            "gap": "Customer or entity segmentation data (size, industry, tenure, segment)",
            "impact": (
                "Cannot determine whether concentration is healthy "
                "(large, stable entities) or risky (small number of "
                "potentially volatile entities)."
            ),
            "suggested_source": "CRM system, customer master data",
        },
        {
            "gap": "Historical concentration trend data (prior periods)",
            "impact": (
                "Cannot assess whether concentration is improving "
                "(diversifying) or worsening (narrowing)."
            ),
            "suggested_source": "Historical financial reports, data warehouse",
        },
    ],
    SignalType.RIGHT_SKEWED: [
        {
            "gap": "Segment-level breakdowns for the top entities",
            "impact": (
                "Cannot distinguish between a few large but stable "
                "contributors and unsustainable one-off spikes."
            ),
            "suggested_source": "Transaction-level data, entity profiles",
        },
    ],
    SignalType.OUTLIER_DETECTED: [
        {
            "gap": "Operational metadata or audit logs for flagged records",
            "impact": (
                "Cannot determine whether outliers are data errors "
                "(fixable) or legitimate rare events (must be monitored)."
            ),
            "suggested_source": "Data entry system, operational database",
        },
    ],
    SignalType.DECREASING_TREND: [
        {
            "gap": "External benchmarks or market data for the same period",
            "impact": (
                "Cannot determine whether the decline is company-specific "
                "or an industry-wide trend."
            ),
            "suggested_source": "Industry reports, market intelligence",
        },
        {
            "gap": "Customer churn or retention data",
            "impact": (
                "Cannot determine whether the decline is due to customer "
                "loss, reduced spend per customer, or fewer new customers."
            ),
            "suggested_source": "CRM system, customer analytics platform",
        },
    ],
    SignalType.INCREASING_TREND: [
        {
            "gap": "Market share or competitive benchmarking data",
            "impact": (
                "Cannot determine whether growth represents share gain "
                "or is simply riding market tailwinds."
            ),
            "suggested_source": "Industry reports, market intelligence",
        },
    ],
    SignalType.HIGH_MISSING_RATE: [
        {
            "gap": "Data collection process documentation or system logs",
            "impact": (
                "Cannot determine whether missing data is a system issue "
                "(fixable with engineering) or a process issue (requires "
                "workflow change)."
            ),
            "suggested_source": "Engineering team, data pipeline documentation",
        },
    ],
    SignalType.LOW_VARIANCE: [
        {
            "gap": "Additional related metrics for the same dimension",
            "impact": (
                "A low-variance column has limited analytical value.  "
                "Without correlated alternative metrics, this dimension "
                "cannot contribute to the investigation."
            ),
            "suggested_source": "Business team, domain experts",
        },
    ],
    SignalType.HIGH_CARDINALITY: [
        {
            "gap": "Hierarchical categorisation or taxonomy for the column",
            "impact": (
                "Cannot aggregate the column into analysis-ready groupings "
                "without a defined hierarchy."
            ),
            "suggested_source": "Data governance team, business glossary",
        },
    ],
    SignalType.LEFT_SKEWED: [
        {
            "gap": "Operational context for low-value records",
            "impact": (
                "Cannot determine whether low values represent "
                "underperformance, special pricing, or measurement errors."
            ),
            "suggested_source": "Operations team, pricing database",
        },
    ],
}

# ---------------------------------------------------------------------------
# Investigation path templates — step-by-step guided exploration
# ---------------------------------------------------------------------------

_PATH_TEMPLATES: dict[SignalType, dict] = {
    SignalType.HIGH_CONCENTRATION: {
        "title": "Investigate concentration risk in {column}",
        "description": (
            "Map the entities driving concentration in '{column}', assess "
            "their stability, and evaluate diversification options."
        ),
        "steps": [
            "Identify the top 5-10 contributors in '{column}' by share of total.",
            "Profile each top contributor: how long have they been top "
            "contributors?  Has their share been growing or shrinking?",
            "Calculate the Herfindahl-Hirschman Index (HHI) for "
            "'{column}' to quantify concentration level objectively.",
            "Segment '{column}' values by size decile and analyse "
            "concentration within each decile.",
            "Estimate the revenue / value impact if the top contributor "
            "were to churn completely.",
            "Develop a monitoring dashboard that tracks concentration "
            "monthly with alerts if it exceeds thresholds.",
        ],
    },
    SignalType.DECREASING_TREND: {
        "title": "Diagnose the decline in {column}",
        "description": (
            "Decompose the declining trend in '{column}' to identify the "
            "root drivers — is it customer loss, reduced spend, or "
            "something else?"
        ),
        "steps": [
            "Break down '{column}' trend by the primary categorical "
            "dimensions (region, product, segment) to isolate where "
            "the decline is happening.",
            "Decompose the change into: (a) change in number of "
            "transactions/customers, (b) change in value per transaction.",
            "Compare the decline rate against prior periods — is it "
            "accelerating or stabilising?",
            "If customer-level data is available, segment customers "
            "into: growing, flat, declining, and churned.  Quantify each.",
            "Interview stakeholders in the affected business areas to "
            "validate the quantitative findings with qualitative context.",
            "Build a recovery scenario model: what would it take to "
            "return '{column}' to the prior level?",
        ],
    },
    SignalType.INCREASING_TREND: {
        "title": "Understand the growth drivers in {column}",
        "description": (
            "Decompose the growth in '{column}' to understand whether "
            "it is sustainable, broad-based, and high-quality."
        ),
        "steps": [
            "Decompose growth into: new customer acquisition, increased "
            "spend per existing customer, and price changes.",
            "Identify which segments (region, product, category) are "
            "driving the growth — is it broad or narrow?",
            "Calculate customer cohort retention: are new customers "
            "staying or is growth driven by one-time purchasers?",
            "Compare growth rate against market / industry benchmarks "
            "if available.",
            "Assess whether the growth is profitable: is the marginal "
            "cost of the growth sustainable?",
            "Set up leading indicators to detect if growth begins to "
            "slow before it appears in aggregate metrics.",
        ],
    },
    SignalType.OUTLIER_DETECTED: {
        "title": "Investigate outlier records in {column}",
        "description": (
            "Review the outlier records in '{column}' to classify them "
            "and determine whether they should be excluded, monitored, "
            "or investigated further."
        ),
        "steps": [
            "Extract all records where '{column}' falls outside the "
            "IQR bounds.",
            "For each outlier, check: what entity, what time period, "
            "what other characteristics?  Look for patterns.",
            "Classify each outlier: (A) data error — fix the source, "
            "(B) legitimate rare event — document and monitor, "
            "(C) unknown — flag for manual review.",
            "Recompute key aggregate metrics (mean, total, trend) with "
            "and without outliers.  Quantify the distortion.",
            "If outliers represent legitimate business events, create a "
            "separate monitoring process for them.",
        ],
    },
    SignalType.RIGHT_SKEWED: {
        "title": "Analyse the right-skewed distribution in {column}",
        "description": (
            "Understand what is causing the right skew in '{column}' "
            "and whether it represents concentration risk."
        ),
        "steps": [
            "Plot the distribution of '{column}' and identify the elbow "
            "point where values become extreme.",
            "Profile the records above the 90th percentile: who are "
            "they, when did they occur, what segments do they belong to?",
            "Calculate what percentage of total '{column}' value is "
            "contributed by the top 1%, 5%, and 10% of records.",
            "Compare mean vs. median over time — is the gap widening "
            "(increasing skew) or narrowing?",
            "If the skew is structural, segment analysis between the "
            "'typical' and 'extreme' populations.",
        ],
    },
    SignalType.LEFT_SKEWED: {
        "title": "Analyse the left-skewed distribution in {column}",
        "description": (
            "Understand what is causing the left skew in '{column}' "
            "and whether it indicates underperformance risk."
        ),
        "steps": [
            "Extract records below the 10th percentile of '{column}' "
            "and profile their characteristics.",
            "Determine whether low values are: (a) measurement errors, "
            "(b) special pricing or discounts, (c) genuine underperformance.",
            "If underperformance: is it concentrated in specific "
            "segments, regions, or time periods?",
            "Quantify the impact: how much would the mean change if "
            "the bottom performers were brought to median level?",
            "Set up monitoring to detect if the low-value tail is "
            "growing over time.",
        ],
    },
    SignalType.HIGH_MISSING_RATE: {
        "title": "Address data quality in {column}",
        "description": (
            "Investigate and remediate the missing data in '{column}' "
            "to improve analytical reliability."
        ),
        "steps": [
            "Identify whether missing values in '{column}' are random "
            "or systematic (correlated with time, category, or other "
            "columns).",
            "If systematic: which segments or time periods are most "
            "affected?  Is this a known data collection gap?",
            "Assess the impact: would imputing the missing values "
            "change key conclusions?",
            "Engage the data owner to understand why data is missing "
            "and whether the collection process can be improved.",
            "If imputation is acceptable, test simple strategies "
            "(mean, median, mode) and document the chosen approach.",
        ],
    },
    SignalType.HIGH_CARDINALITY: {
        "title": "Reduce cardinality in {column} for analysis",
        "description": (
            "Transform '{column}' from a high-cardinality field into "
            "analysis-ready categories."
        ),
        "steps": [
            "Review the distinct values in '{column}' — are there "
            "obvious groupings or hierarchies?",
            "Check for near-duplicates or inconsistent naming that "
            "inflates the unique count.",
            "If '{column}' is an identifier: exclude it from "
            "dimensional analysis and use it only for joins or "
            "deduplication.",
            "If '{column}' should be categorical: apply binning "
            "(frequency-based, value-based, or business-rule-based).",
            "Validate the reduced categories with a domain expert "
            "before using them in reporting.",
        ],
    },
    SignalType.LOW_VARIANCE: {
        "title": "Evaluate analytical value of {column}",
        "description": (
            "Determine whether '{column}' should remain in the "
            "analytical dataset given its low discriminatory power."
        ),
        "steps": [
            "Confirm that the low variance is genuine and not an "
            "artifact of data truncation or default values.",
            "Check whether '{column}' is expected to vary — if so, "
            "the lack of variance is ITSELF a finding.",
            "If the column is genuinely static: deprioritise it in "
            "segmentation and analysis.",
            "Identify alternative metrics that measure the same "
            "business concept with more granularity.",
            "Document the decision to include or exclude '{column}' "
            "so future analysts understand the rationale.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Alternative explanation templates — for REFUTED hypotheses
# ---------------------------------------------------------------------------

_ALTERNATIVE_TEMPLATES: dict[SignalType, list[str]] = {
    SignalType.RIGHT_SKEWED: [
        "The distribution of '{column}' may have a natural upper bound "
        "that was not considered — check whether the 'extreme' values "
        "are actually within normal operating range.",
        "The right skew may be an artifact of how '{column}' is "
        "calculated (e.g., aggregated from higher-frequency data) "
        "rather than a real business pattern.",
    ],
    SignalType.OUTLIER_DETECTED: [
        "The IQR method may be too sensitive for '{column}' — consider "
        "using a different outlier detection method (z-score, MAD, "
        "or percentile-based).",
        "The 'outliers' may represent a legitimate sub-population rather "
        "than anomalous records — investigate whether they share common "
        "characteristics.",
    ],
    SignalType.DECREASING_TREND: [
        "The apparent decline in '{column}' may be seasonal rather than "
        "structural — extend the analysis to multiple seasonal cycles.",
        "A change in data collection or reporting methodology may "
        "explain the trend — verify that definitions have been "
        "consistent over the analysis period.",
    ],
    SignalType.INCREASING_TREND: [
        "Growth in '{column}' may reflect a one-time event (acquisition, "
        "promotion, pricing change) rather than organic momentum.",
        "The trend may be inflated by a small number of outlier "
        "transactions — check whether the median shows the same pattern.",
    ],
    SignalType.HIGH_CONCENTRATION: [
        "Concentration may be industry-typical — compare against "
        "available benchmarks before concluding it is a risk.",
        "The categorical grouping in '{column}' may be too granular, "
        "creating artificial concentration — try broader groupings.",
    ],
}

# ---------------------------------------------------------------------------
# Cross-pattern analysis
# ---------------------------------------------------------------------------

_CROSS_PATTERN_QUESTIONS: dict[frozenset[SignalType], list[dict]] = {
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED}): [
        {
            "question": (
                "Are the same entities driving both the right skew and "
                "the high concentration?  If so, the business is "
                "structurally dependent on a very small group."
            ),
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.OUTLIER_DETECTED, SignalType.RIGHT_SKEWED}): [
        {
            "question": (
                "Are the detected outliers the CAUSE of the right skew?  "
                "If you remove the outliers, does the distribution become "
                "symmetric?"
            ),
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.DECREASING_TREND}): [
        {
            "question": (
                "Is the decline driven by the top contributors losing "
                "value, or is the long tail shrinking?  The response "
                "strategy is fundamentally different."
            ),
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.INCREASING_TREND}): [
        {
            "question": (
                "Is the growth concentrated in the already-dominant "
                "entities?  If so, concentration is increasing alongside "
                "growth — a compounding risk."
            ),
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_MISSING_RATE, SignalType.OUTLIER_DETECTED}): [
        {
            "question": (
                "Could the missing data be creating artificial outliers?  "
                "If missing values are being defaulted to zero or extreme "
                "values, both signals may share a root cause."
            ),
            "category": "cross_pattern",
        },
    ],
}


# ---------------------------------------------------------------------------
# The interactive investigator
# ---------------------------------------------------------------------------


class InteractiveInvestigator:
    """Produces a forward-looking InteractiveInvestigationReport from a
    deterministic InvestigationReport.

    Usage:
        investigator = InteractiveInvestigator()
        interactive = investigator.investigate(report)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def investigate(
        self,
        report: InvestigationReport,
    ) -> InteractiveInvestigationReport:
        """Generate the interactive investigation report.

        Args:
            report: The deterministic pipeline output with findings,
                    executive summary, and next steps.

        Returns:
            An InteractiveInvestigationReport with follow-up questions,
            data gaps, investigation paths, and unresolved areas.
        """
        findings = report.findings

        follow_ups = self._generate_follow_up_questions(findings)
        data_gaps = self._identify_data_gaps(findings)
        paths = self._build_investigation_paths(findings)
        unresolved = self._collect_unresolved(findings)

        return InteractiveInvestigationReport(
            follow_up_questions=follow_ups,
            data_gaps=data_gaps,
            investigation_paths=paths,
            unresolved_areas=unresolved,
        )

    # ------------------------------------------------------------------
    # Follow-up questions
    # ------------------------------------------------------------------

    def _generate_follow_up_questions(
        self,
        findings: list[Finding],
    ) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []

        for f in findings:
            # Determine the signal type from the finding title/context.
            # The finding title contains the hypothesis title, which
            # includes the signal column.  We use the observation and
            # status to generate appropriate follow-ups.
            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue

            related = [f.title]

            if f.status == HypothesisStatus.SUPPORTED:
                questions.extend(
                    self._drill_down_questions(signal_type, f, related)
                )

            elif f.status == HypothesisStatus.REFUTED:
                questions.extend(
                    self._alternative_questions(signal_type, f, related)
                )

            elif f.status == HypothesisStatus.INCONCLUSIVE:
                questions.extend(
                    self._inconclusive_questions(signal_type, f, related)
                )

        # Cross-pattern questions
        signal_types = {
            self._infer_signal_type(f)
            for f in findings
        }
        signal_types.discard(None)
        questions.extend(
            self._cross_pattern_questions(signal_types, findings)
        )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        questions.sort(key=lambda q: priority_order.get(q.priority, 2))

        # Deduplicate by question text
        seen: set[str] = set()
        unique: list[FollowUpQuestion] = []
        for q in questions:
            if q.question not in seen:
                seen.add(q.question)
                unique.append(q)
        return unique

    def _drill_down_questions(
        self,
        signal_type: SignalType,
        finding: Finding,
        related: list[str],
    ) -> list[FollowUpQuestion]:
        templates = _DRILL_DOWN_TEMPLATES.get(signal_type, [])
        return [
            FollowUpQuestion(
                question=t["question"].format(
                    column=self._extract_column(finding)
                ),
                priority=self._confidence_to_priority(finding),
                category=t["category"],
                related_finding_titles=related,
                required_data=[
                    d.format(column=self._extract_column(finding))
                    for d in t.get("required_data", [])
                ],
            )
            for t in templates[:2]  # top 2 most relevant
        ]

    def _alternative_questions(
        self,
        signal_type: SignalType,
        finding: Finding,
        related: list[str],
    ) -> list[FollowUpQuestion]:
        templates = _ALTERNATIVE_TEMPLATES.get(signal_type, [])
        return [
            FollowUpQuestion(
                question=t.format(column=self._extract_column(finding)),
                priority="medium",
                category="alternative_explanation",
                related_finding_titles=related,
                required_data=[],
            )
            for t in templates[:1]  # top 1 to avoid overload
        ]

    def _inconclusive_questions(
        self,
        signal_type: SignalType,
        finding: Finding,
        related: list[str],
    ) -> list[FollowUpQuestion]:
        return [
            FollowUpQuestion(
                question=(
                    f"What additional data or analysis would help resolve "
                    f"the inconclusive finding '{finding.title}'?"
                ),
                priority="medium",
                category="data_gap",
                related_finding_titles=related,
                required_data=[
                    f"additional data for {self._extract_column(finding)}",
                    "longer time horizon or more granular breakdowns",
                ],
            )
        ]

    def _cross_pattern_questions(
        self,
        signal_types: set[SignalType],
        findings: list[Finding],
    ) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []
        all_titles = [f.title for f in findings]

        for key, templates in _CROSS_PATTERN_QUESTIONS.items():
            if key.issubset(signal_types):
                for t in templates:
                    questions.append(
                        FollowUpQuestion(
                            question=t["question"],
                            priority="high",
                            category=t["category"],
                            related_finding_titles=list(all_titles),
                            required_data=[],
                        )
                    )
        return questions

    # ------------------------------------------------------------------
    # Data gaps
    # ------------------------------------------------------------------

    def _identify_data_gaps(
        self,
        findings: list[Finding],
    ) -> list[DataGap]:
        gaps: list[DataGap] = []
        seen_gaps: set[str] = set()

        for f in findings:
            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue

            templates = _DATA_GAP_TEMPLATES.get(signal_type, [])
            for t in templates:
                if t["gap"] in seen_gaps:
                    continue
                seen_gaps.add(t["gap"])
                gaps.append(
                    DataGap(
                        gap=t["gap"],
                        impact=t["impact"],
                        affected_hypotheses=[f.title],
                        suggested_source=t["suggested_source"],
                    )
                )

        return gaps

    # ------------------------------------------------------------------
    # Investigation paths
    # ------------------------------------------------------------------

    def _build_investigation_paths(
        self,
        findings: list[Finding],
    ) -> list[InvestigationPath]:
        paths: list[InvestigationPath] = []

        # Only build paths for SUPPORTED findings with HIGH or MEDIUM
        # confidence — these are the ones worth exploring further.
        for f in findings:
            if f.status != HypothesisStatus.SUPPORTED:
                continue

            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue

            template = _PATH_TEMPLATES.get(signal_type)
            if template is None:
                continue

            column = self._extract_column(f)
            paths.append(
                InvestigationPath(
                    title=template["title"].format(column=column),
                    description=template["description"].format(
                        column=column
                    ),
                    steps=[
                        s.format(column=column)
                        for s in template["steps"]
                    ],
                    starting_finding=f.title,
                )
            )

        # Limit to top 5 paths to avoid overwhelming
        return paths[:5]

    # ------------------------------------------------------------------
    # Unresolved areas
    # ------------------------------------------------------------------

    def _collect_unresolved(
        self,
        findings: list[Finding],
    ) -> list[str]:
        return [
            f.title
            for f in findings
            if f.status == HypothesisStatus.INCONCLUSIVE
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _infer_signal_type(self, finding: Finding) -> SignalType | None:
        """Infer the SignalType from a Finding's supporting evidence.

        Each Evidence item has a `supporting_signal` field that links it
        to the SignalType that triggered the hypothesis.  We extract the
        signal type from the first piece of supporting evidence.
        """
        for e in finding.supporting_evidence:
            if e.supporting_signal is not None:
                return e.supporting_signal
        for e in finding.contradicting_evidence:
            if e.supporting_signal is not None:
                return e.supporting_signal
        return None

    def _extract_column(self, finding: Finding) -> str:
        """Extract the primary column name from a finding's evidence."""
        for e in finding.supporting_evidence:
            if e.related_column:
                return e.related_column
        for e in finding.contradicting_evidence:
            if e.related_column:
                return e.related_column
        return "unknown_column"

    @staticmethod
    def _confidence_to_priority(finding: Finding) -> str:
        """Map HypothesisConfidence to a priority string."""
        confidence = finding.confidence.value
        if confidence == "high":
            return "high"
        elif confidence == "medium":
            return "medium"
        return "low"
