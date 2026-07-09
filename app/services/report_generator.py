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
)


# ---------------------------------------------------------------------------
# Finding templates — one entry per (SignalType × HypothesisStatus)
#
# Placeholders like {column}, {mean}, {skewness}, etc. are filled from
# evidence metric values at generation time.
# ---------------------------------------------------------------------------

_FINDING_TEMPLATES: dict[SignalType, dict[HypothesisStatus, dict[str, str]]] = {
    # -- RIGHT_SKEWED -------------------------------------------------------
    SignalType.RIGHT_SKEWED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' exhibits a right-skewed distribution: "
                "mean ({mean}) is significantly higher than median ({median}), "
                "skewness={skewness}."
            ),
            "analysis": (
                "The positive skewness coefficient ({skewness}) confirms that "
                "a small number of high-value records are pulling the average "
                "well above the typical value. The mean is not representative "
                "of the majority of observations."
            ),
            "business_impact": (
                "Business averages may be misleading for decision-making. "
                "Performance metrics based on means alone will overstate "
                "typical outcomes. The business may be dependent on a small "
                "number of high-value transactions, customers, or products."
            ),
            "recommendation": (
                "Segment '{column}' to separate high-value outliers from the "
                "typical population. Use median-based metrics for baseline "
                "reporting. Investigate whether high-value records represent "
                "sustainable business or one-off events."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for possible right-skewed "
                "distribution, but the skewness coefficient ({skewness}) does "
                "not confirm a meaningful right skew."
            ),
            "analysis": (
                "The statistical evidence does not support the right-skew "
                "hypothesis. The distribution may be approximately symmetric "
                "or the sample may be too small to detect skew."
            ),
            "business_impact": (
                "No evidence of head-heavy concentration risk in this "
                "dimension. Standard statistical measures (mean, standard "
                "deviation) are likely appropriate for reporting."
            ),
            "recommendation": (
                "No immediate action required. Re-evaluate if data volume "
                "increases or if business context suggests hidden "
                "concentration risk."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible right-skewed "
                "distribution, but evidence was insufficient to confirm or "
                "refute the pattern."
            ),
            "analysis": (
                "Available metrics could not conclusively validate the skew "
                "hypothesis. This may be due to insufficient data, missing "
                "metric values, or a borderline distribution."
            ),
            "business_impact": (
                "Cannot determine whether business averages are reliable "
                "for this dimension. Decisions based on '{column}' means "
                "should be made with caution."
            ),
            "recommendation": (
                "Collect more data or review data quality for '{column}'. "
                "Consider manual inspection of the distribution before "
                "drawing business conclusions."
            ),
        },
    },
    # -- LEFT_SKEWED --------------------------------------------------------
    SignalType.LEFT_SKEWED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' exhibits a left-skewed distribution: "
                "mean ({mean}) is below median ({median}), "
                "skewness={skewness}."
            ),
            "analysis": (
                "The negative skewness coefficient ({skewness}) indicates "
                "that a small number of unusually low values are pulling "
                "the average downward. The mean understates the typical value."
            ),
            "business_impact": (
                "Business averages may understate typical performance. "
                "A small number of underperforming records could be "
                "distorting overall metrics. If these represent real "
                "business events, they warrant investigation."
            ),
            "recommendation": (
                "Investigate the low-value records in '{column}' to "
                "determine whether they reflect data errors, special "
                "cases, or systemic underperformance. Exclude or segment "
                "them for cleaner reporting."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for possible left-skewed "
                "distribution, but the skewness coefficient ({skewness}) does "
                "not confirm a meaningful left skew."
            ),
            "analysis": (
                "The statistical evidence does not support the left-skew "
                "hypothesis. The distribution may be approximately symmetric."
            ),
            "business_impact": (
                "No evidence of systemic underperformance bias in this "
                "dimension. Standard reporting metrics should be reliable."
            ),
            "recommendation": (
                "No immediate action required. Re-evaluate if new data "
                "suggests emerging low-end outliers."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible left-skewed "
                "distribution, but evidence was insufficient to confirm or "
                "refute the pattern."
            ),
            "analysis": (
                "Available metrics could not conclusively validate the "
                "left-skew hypothesis. The distribution may be borderline."
            ),
            "business_impact": (
                "Cannot determine whether low-value records are materially "
                "distorting '{column}' averages."
            ),
            "recommendation": (
                "Collect more data or manually inspect the distribution "
                "of '{column}'."
            ),
        },
    },
    # -- OUTLIER_DETECTED ---------------------------------------------------
    SignalType.OUTLIER_DETECTED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' contains {outlier_count} outlier(s), "
                "representing {outlier_ratio:.1%} of values. IQR bounds: "
                "[{iqr_lower_bound}, {iqr_upper_bound}]."
            ),
            "analysis": (
                "The presence of {outlier_count} outlier(s) ({outlier_ratio:.1%} "
                "of data) confirms unusual values exist in '{column}'. "
                "These may reflect real business events, data entry errors, "
                "or rare but legitimate transactions."
            ),
            "business_impact": (
                "Outliers can significantly distort aggregated metrics "
                "(totals, averages) and lead to incorrect business decisions "
                "if not properly handled. If the outliers represent real "
                "events, they may indicate emerging risks or opportunities."
            ),
            "recommendation": (
                "Review the {outlier_count} outlier record(s) in '{column}' "
                "individually. Classify each as: data error (fix), legitimate "
                "rare event (document), or unknown (flag for monitoring). "
                "Consider excluding outliers from baseline reporting."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for outliers, but evidence "
                "shows {outlier_count} outlier(s), which does not confirm "
                "a meaningful anomaly pattern."
            ),
            "analysis": (
                "The outlier detection signal was not validated by the "
                "evidence. Any flagged values may fall within expected "
                "bounds or represent normal variability."
            ),
            "business_impact": (
                "No confirmed outlier risk in '{column}'. Standard "
                "reporting can proceed without special handling."
            ),
            "recommendation": (
                "No immediate action required. Continue monitoring "
                "'{column}' for emerging outliers in future data loads."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible outliers, but "
                "evidence was insufficient to confirm or refute."
            ),
            "analysis": (
                "Insufficient data or metrics to validate the outlier "
                "signal for '{column}'."
            ),
            "business_impact": (
                "Cannot determine whether outliers materially affect "
                "'{column}' metrics."
            ),
            "recommendation": (
                "Collect more data or manually inspect '{column}' for "
                "unusual values."
            ),
        },
    },
    # -- INCREASING_TREND ---------------------------------------------------
    SignalType.INCREASING_TREND: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' shows an increasing trend: changed from "
                "{first_val} to {last_val} (growth rate: {growth_rate:.1%})."
            ),
            "analysis": (
                "The positive growth rate of {growth_rate:.1%} confirms an "
                "upward trajectory in '{column}'. This trend may be driven "
                "by organic growth, market expansion, or pricing changes."
            ),
            "business_impact": (
                "Sustained growth in '{column}' is a positive signal but "
                "requires understanding of the drivers. If growth is "
                "concentrated in a few segments, it may not be sustainable. "
                "If broad-based, it indicates healthy business momentum."
            ),
            "recommendation": (
                "Decompose the growth in '{column}' by segment (region, "
                "product, customer cohort) to identify drivers. Assess "
                "whether the growth rate is accelerating, stable, or "
                "decelerating."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for an increasing trend, but "
                "the growth rate ({growth_rate:.1%}) does not confirm a "
                "meaningful upward trajectory."
            ),
            "analysis": (
                "The observed change in '{column}' is too small or "
                "inconsistent to confirm a genuine increasing trend."
            ),
            "business_impact": (
                "No confirmed growth trend in '{column}'. Business "
                "planning should not assume upward momentum in this "
                "dimension without further evidence."
            ),
            "recommendation": (
                "Monitor '{column}' over a longer time horizon to detect "
                "whether a trend emerges. A single-period change may not "
                "be indicative."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for a possible increasing "
                "trend, but evidence was insufficient to validate."
            ),
            "analysis": (
                "Insufficient data points or metrics to confirm or refute "
                "the increasing trend in '{column}'."
            ),
            "business_impact": (
                "Cannot determine whether '{column}' is genuinely trending "
                "upward."
            ),
            "recommendation": (
                "Collect more time-series data for '{column}' to enable "
                "trend validation."
            ),
        },
    },
    # -- DECREASING_TREND ---------------------------------------------------
    SignalType.DECREASING_TREND: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' shows a decreasing trend: changed from "
                "{first_val} to {last_val} (change: {growth_rate:.1%})."
            ),
            "analysis": (
                "The negative growth rate of {growth_rate:.1%} confirms a "
                "downward trajectory in '{column}'. This may indicate "
                "customer churn, demand decline, competitive pressure, or "
                "a deliberate business shift."
            ),
            "business_impact": (
                "A sustained decline in '{column}' represents a business "
                "risk. If the trend continues without intervention, it "
                "may lead to significant revenue or volume loss. Early "
                "diagnosis of the cause is critical."
            ),
            "recommendation": (
                "Investigate the drivers of decline in '{column}': break "
                "down by segment to identify whether the decline is "
                "broad-based or concentrated. Compare against market "
                "benchmarks if available. Develop a retention or "
                "turnaround plan."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for a decreasing trend, but "
                "the change ({growth_rate:.1%}) does not confirm a "
                "meaningful decline."
            ),
            "analysis": (
                "The observed change in '{column}' is too small or "
                "inconsistent to confirm a genuine decreasing trend."
            ),
            "business_impact": (
                "No confirmed decline in '{column}'. Business planning "
                "should not assume negative momentum without further "
                "evidence."
            ),
            "recommendation": (
                "Monitor '{column}' over a longer time horizon. A "
                "short-term dip may not indicate a structural trend."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for a possible decreasing "
                "trend, but evidence was insufficient to validate."
            ),
            "analysis": (
                "Insufficient data points or metrics to confirm or refute "
                "the decreasing trend in '{column}'."
            ),
            "business_impact": (
                "Cannot determine whether '{column}' is genuinely declining."
            ),
            "recommendation": (
                "Collect more time-series data for '{column}' to enable "
                "trend validation."
            ),
        },
    },
    # -- HIGH_CONCENTRATION -------------------------------------------------
    SignalType.HIGH_CONCENTRATION: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' shows high concentration: the top "
                "contributor accounts for {top_1_share:.1%} of the total, "
                "and the top 3 account for {top_3_share:.1%}."
            ),
            "analysis": (
                "With {top_1_share:.1%} of value concentrated in a single "
                "category, the business has significant dependency risk. "
                "The top-3 cumulative share of {top_3_share:.1%} confirms "
                "this is a structural pattern, not a single outlier."
            ),
            "business_impact": (
                "High concentration means business performance is heavily "
                "dependent on a small number of entities (customers, "
                "products, or regions). Any change affecting the top "
                "contributor(s) would have a disproportionate impact on "
                "overall results. This is a key business risk."
            ),
            "recommendation": (
                "Assess the stability and retention risk of the top "
                "contributors in '{column}'. Develop diversification "
                "strategies if concentration exceeds risk tolerance. "
                "Set up early-warning monitoring for the top entities."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for possible concentration, "
                "but the top contributor share ({top_1_share:.1%}) does not "
                "confirm a meaningful concentration risk."
            ),
            "analysis": (
                "The concentration level in '{column}' is within acceptable "
                "bounds. No single category dominates the distribution."
            ),
            "business_impact": (
                "Business performance is reasonably diversified across "
                "'{column}' categories. No immediate concentration risk."
            ),
            "recommendation": (
                "Periodically review concentration levels in '{column}' "
                "as the business mix evolves."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible concentration, "
                "but evidence was insufficient to validate."
            ),
            "analysis": (
                "Cannot determine the true concentration level in "
                "'{column}' from available evidence."
            ),
            "business_impact": (
                "Unable to assess concentration risk in '{column}'. "
                "Decisions about diversification may be premature."
            ),
            "recommendation": (
                "Collect more granular data for '{column}' or verify "
                "category definitions before assessing concentration."
            ),
        },
    },
    # -- HIGH_MISSING_RATE --------------------------------------------------
    SignalType.HIGH_MISSING_RATE: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' has a missing rate of "
                "{null_percentage:.1f}%."
            ),
            "analysis": (
                "A missing rate of {null_percentage:.1f}% is materially "
                "high and may compromise the reliability of any analysis "
                "involving '{column}'. The missing data may be random or "
                "systematic — the latter is more dangerous as it introduces "
                "bias."
            ),
            "business_impact": (
                "Conclusions drawn from '{column}' may be unreliable or "
                "biased. If this column is used for business decisions "
                "(e.g., revenue reporting, customer scoring), the missing "
                "data could lead to incorrect actions."
            ),
            "recommendation": (
                "Investigate the root cause of missing data in '{column}': "
                "is it a data collection gap, a system issue, or a "
                "legitimate 'not applicable' case? If the data is critical, "
                "consider imputation strategies or process fixes to reduce "
                "the missing rate."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for a high missing rate, but "
                "the actual rate ({null_percentage:.1f}%) is within "
                "acceptable bounds."
            ),
            "analysis": (
                "The missing data rate in '{column}' is low enough that "
                "it is unlikely to materially affect analysis results."
            ),
            "business_impact": (
                "Data quality in '{column}' is adequate for business "
                "reporting and analysis."
            ),
            "recommendation": (
                "Continue monitoring '{column}' missing rate as part of "
                "routine data quality checks."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for a possible high missing "
                "rate, but evidence was insufficient to validate."
            ),
            "analysis": (
                "Cannot determine the true missing data rate or its "
                "impact for '{column}'."
            ),
            "business_impact": (
                "Data quality in '{column}' is uncertain. Use caution "
                "when relying on this column for decisions."
            ),
            "recommendation": (
                "Verify the missing data calculation for '{column}' and "
                "assess whether missing values are random or systematic."
            ),
        },
    },
    # -- HIGH_CARDINALITY ---------------------------------------------------
    SignalType.HIGH_CARDINALITY: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' has {unique_count} unique values "
                "({unique_ratio:.1%} of rows)."
            ),
            "analysis": (
                "With a uniqueness ratio of {unique_ratio:.1%}, '{column}' "
                "behaves more like an identifier than a categorical "
                "dimension. It has too many distinct values to be useful "
                "for grouping or aggregation."
            ),
            "business_impact": (
                "'{column}' cannot be effectively used as an analytical "
                "dimension in its current form. Attempting to group or "
                "aggregate by this column will produce meaningless results "
                "(one row per group)."
            ),
            "recommendation": (
                "Determine whether '{column}' is an identifier (exclude "
                "from analysis) or should be aggregated into broader "
                "categories. If categorical, consider binning, clustering, "
                "or extracting higher-level groupings."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for high cardinality, but "
                "the uniqueness ratio ({unique_ratio:.1%}) is within "
                "acceptable bounds."
            ),
            "analysis": (
                "'{column}' has a reasonable number of distinct values "
                "for use as a grouping dimension."
            ),
            "business_impact": (
                "'{column}' is suitable for use as an analytical "
                "dimension in reporting and aggregation."
            ),
            "recommendation": (
                "No action required. '{column}' can be used normally "
                "for grouping and segmentation."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible high "
                "cardinality, but evidence was insufficient to validate."
            ),
            "analysis": (
                "Cannot determine whether '{column}' uniqueness is "
                "problematic for analytical use."
            ),
            "business_impact": (
                "Use caution when grouping by '{column}' — results may "
                "be overly granular."
            ),
            "recommendation": (
                "Review the distinct values in '{column}' to determine "
                "if binning or categorization is needed."
            ),
        },
    },
    # -- LOW_VARIANCE -------------------------------------------------------
    SignalType.LOW_VARIANCE: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Column '{column}' has very low variance: coefficient of "
                "variation = {coefficient_of_variation:.2%}, "
                "std = {std}."
            ),
            "analysis": (
                "A coefficient of variation of {coefficient_of_variation:.2%} "
                "indicates that '{column}' values barely deviate from the "
                "mean. This column has almost no discriminatory power."
            ),
            "business_impact": (
                "'{column}' provides little analytical value — it cannot "
                "differentiate between good and bad performers, identify "
                "trends, or segment populations. Including it in analysis "
                "adds noise without insight."
            ),
            "recommendation": (
                "Consider deprioritizing or excluding '{column}' from "
                "active analysis. If the column was expected to vary "
                "(e.g., customer ratings, prices), investigate why it is "
                "static — this may itself be a finding."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "Column '{column}' was flagged for low variance, but the "
                "coefficient of variation ({coefficient_of_variation:.2%}) "
                "does not confirm a problem."
            ),
            "analysis": (
                "'{column}' shows sufficient variability to be analytically "
                "useful."
            ),
            "business_impact": (
                "'{column}' has adequate discriminatory power for "
                "segmentation and analysis."
            ),
            "recommendation": (
                "No action required. '{column}' can be used normally "
                "in analysis."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Column '{column}' was flagged for possible low variance, "
                "but evidence was insufficient to validate."
            ),
            "analysis": (
                "Cannot determine whether '{column}' variance is "
                "analytically adequate."
            ),
            "business_impact": (
                "The analytical value of '{column}' is uncertain."
            ),
            "recommendation": (
                "Collect more data or review '{column}' values manually "
                "to assess variance."
            ),
        },
    },
}

# ---------------------------------------------------------------------------
# Composite-hypothesis templates
#
# Composite hypotheses combine multiple signal types. Templates are keyed
# by frozen set of signal types to match regardless of order.
# ---------------------------------------------------------------------------

_COMPOSITE_TEMPLATES: dict[frozenset[SignalType], dict[HypothesisStatus, dict[str, str]]] = {
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "The dataset shows both high concentration and right-skewed "
                "distribution in related dimensions. This indicates that a "
                "small number of entities dominate business results."
            ),
            "analysis": (
                "The co-occurrence of concentration and right skew is a "
                "strong signal of head-heavy business structure. A small "
                "number of high-value records are disproportionately "
                "driving aggregate metrics."
            ),
            "business_impact": (
                "The business is structurally dependent on a small number "
                "of entities. This creates fragility — any change in the "
                "top contributors will have outsized impact on overall "
                "performance. Growth may also be concentrated rather than "
                "broad-based."
            ),
            "recommendation": (
                "This is a high-priority finding. Map the top contributors "
                "and assess their stability. Develop a diversification "
                "strategy and set up concentration monitoring as a key "
                "risk indicator. Segment reporting should separate top "
                "contributors from the long tail."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "The combined concentration and right-skew pattern was "
                "not confirmed by available evidence."
            ),
            "analysis": (
                "The evidence does not support the hypothesis of combined "
                "concentration and skew risk. The business structure may "
                "be more balanced than initially suspected."
            ),
            "business_impact": (
                "No confirmed structural dependency risk from the "
                "concentration-skew combination."
            ),
            "recommendation": (
                "Re-evaluate if new data becomes available. For now, "
                "standard monitoring is sufficient."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Possible combined concentration and skew pattern, but "
                "evidence is insufficient to confirm or refute."
            ),
            "analysis": (
                "Some signals suggest head-heavy structure, but evidence "
                "is incomplete or mixed."
            ),
            "business_impact": (
                "Potential structural dependency risk — cannot be "
                "confirmed or ruled out."
            ),
            "recommendation": (
                "Collect more granular data and re-run the analysis. "
                "In the interim, review top-contributor concentration "
                "manually."
            ),
        },
    },
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.INCREASING_TREND}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Business growth is occurring alongside high concentration. "
                "Growth may be driven primarily by a small number of entities."
            ),
            "analysis": (
                "The combination of increasing trend and high concentration "
                "suggests that growth is not broad-based. A few top "
                "contributors may be responsible for most of the upward "
                "momentum."
            ),
            "business_impact": (
                "Growth that depends on a few entities is fragile. If the "
                "top contributors stall or churn, overall growth could "
                "reverse quickly. Reported growth rates may overstate the "
                "health of the broader business."
            ),
            "recommendation": (
                "Decompose growth into contributions from top entities vs. "
                "the rest. Assess whether the growth concentration is "
                "increasing over time. Consider strategies to broaden "
                "growth across the base."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "The combined concentration-growth pattern was not "
                "confirmed by available evidence."
            ),
            "analysis": (
                "Evidence does not support the hypothesis that growth is "
                "concentrated in a few entities."
            ),
            "business_impact": (
                "Growth appears to be reasonably distributed. No "
                "confirmed concentration-driven growth risk."
            ),
            "recommendation": (
                "Continue monitoring. Re-evaluate if concentration "
                "metrics change."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Possible growth concentration pattern, but evidence is "
                "insufficient to validate."
            ),
            "analysis": (
                "Some signals suggest growth may be concentrated, but "
                "evidence is incomplete."
            ),
            "business_impact": (
                "Growth quality is uncertain — cannot determine whether "
                "growth is broad-based or narrow."
            ),
            "recommendation": (
                "Collect segment-level trend data to assess growth "
                "distribution."
            ),
        },
    },
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.DECREASING_TREND}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Business decline is occurring in a highly concentrated "
                "structure. The decline may be driven by the top "
                "contributors."
            ),
            "analysis": (
                "When high concentration coexists with a decreasing trend, "
                "it suggests that the dominant entities are experiencing "
                "decline, pulling overall results down. This is a "
                "higher-risk pattern than broad-based decline."
            ),
            "business_impact": (
                "The business faces a dual risk: dependency on a few "
                "entities AND those entities are declining. If the trend "
                "continues, the impact will be magnified by the "
                "concentration. This warrants urgent attention."
            ),
            "recommendation": (
                "Prioritize retention and turnaround efforts for the top "
                "declining entities. Simultaneously, accelerate "
                "diversification to reduce dependency. Set up real-time "
                "monitoring for the top contributors."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "The combined concentration-decline pattern was not "
                "confirmed by available evidence."
            ),
            "analysis": (
                "Evidence does not support the hypothesis that decline is "
                "concentrated in top entities."
            ),
            "business_impact": (
                "The observed decline may be broad-based rather than "
                "driven by top-entity weakness."
            ),
            "recommendation": (
                "Investigate decline drivers across all segments, not "
                "just top entities."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Possible concentration-driven decline, but evidence is "
                "insufficient to validate."
            ),
            "analysis": (
                "Signals suggest top-entity decline risk, but evidence "
                "is incomplete."
            ),
            "business_impact": (
                "Risk of concentrated decline cannot be confirmed or "
                "ruled out."
            ),
            "recommendation": (
                "Collect entity-level trend data to assess whether "
                "decline is concentrated."
            ),
        },
    },
    frozenset({SignalType.OUTLIER_DETECTED, SignalType.RIGHT_SKEWED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "Outliers and right-skewed distribution are present "
                "together, suggesting extreme high values are distorting "
                "overall statistics."
            ),
            "analysis": (
                "The combination of detected outliers and right skew "
                "indicates that extreme values are not just present but "
                "materially affecting the data distribution. These "
                "outliers are likely the cause of the observed skew."
            ),
            "business_impact": (
                "Reported averages and totals may be significantly "
                "inflated by a small number of extreme records. Business "
                "decisions based on these aggregates may be overly "
                "optimistic. The 'typical' performance is likely lower "
                "than reported means suggest."
            ),
            "recommendation": (
                "Review the outlier records individually. Determine "
                "whether they are legitimate (keep and document), errors "
                "(correct or remove), or one-time events (exclude from "
                "baseline). Recompute key metrics with and without "
                "outliers to quantify the distortion."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "The combined outlier-skew pattern was not confirmed by "
                "available evidence."
            ),
            "analysis": (
                "Evidence does not support a material distortion from "
                "extreme values."
            ),
            "business_impact": (
                "Reported statistics are likely representative of the "
                "underlying business reality."
            ),
            "recommendation": (
                "No immediate action required. Standard outlier "
                "monitoring is sufficient."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Possible outlier-driven skew, but evidence is "
                "insufficient to validate."
            ),
            "analysis": (
                "Outlier and skew signals are present but evidence "
                "is incomplete or mixed."
            ),
            "business_impact": (
                "Cannot determine whether extreme values materially "
                "distort business metrics."
            ),
            "recommendation": (
                "Manually review flagged outlier records to assess "
                "their business significance."
            ),
        },
    },
    frozenset({SignalType.HIGH_MISSING_RATE, SignalType.OUTLIER_DETECTED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "High missing data rates and outliers are present in "
                "the same dataset, suggesting data quality issues may "
                "be affecting analytical reliability."
            ),
            "analysis": (
                "The co-occurrence of missing data and outliers is a "
                "red flag for data quality. Missing values may be "
                "creating artificial outliers, or the same underlying "
                "process issues may be causing both problems."
            ),
            "business_impact": (
                "Analysis results may be unreliable due to compounding "
                "data quality issues. Decisions based on this data carry "
                "elevated risk of being incorrect. The root cause may "
                "be a systemic data collection or processing problem."
            ),
            "recommendation": (
                "Prioritize a data quality review. Investigate whether "
                "the missing data and outliers share a common cause "
                "(e.g., system errors, process gaps). Address data "
                "quality before drawing business conclusions from "
                "affected columns."
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "The combined data-quality risk pattern was not "
                "confirmed by available evidence."
            ),
            "analysis": (
                "Evidence does not support the hypothesis of compounding "
                "data quality issues."
            ),
            "business_impact": (
                "Data quality appears adequate for reliable analysis."
            ),
            "recommendation": (
                "Continue routine data quality monitoring."
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "Possible compounding data quality issues, but evidence "
                "is insufficient to validate."
            ),
            "analysis": (
                "Missing data and outlier signals exist but cannot be "
                "conclusively linked."
            ),
            "business_impact": (
                "Data reliability is uncertain — use caution in "
                "business decisions based on affected columns."
            ),
            "recommendation": (
                "Conduct a manual data quality assessment of the "
                "affected columns."
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _build_context(vh: ValidatedHypothesis) -> dict:
    """Extract format placeholders from a validated hypothesis's evidence."""
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
    """Safely format a template string with context values."""
    try:
        return template.format(**ctx)
    except (KeyError, ValueError):
        # Fall back to unformatted template if placeholders are missing
        return template


# ---------------------------------------------------------------------------
# Finding builders
# ---------------------------------------------------------------------------

def _build_simple_finding(vh: ValidatedHypothesis) -> Finding:
    """Build a Finding for a non-composite hypothesis."""
    signal_type = vh.hypothesis.supporting_signals[0]
    status = vh.status
    ctx = _build_context(vh)

    templates = _FINDING_TEMPLATES.get(signal_type, {}).get(status)
    if templates is None:
        # Fallback for any uncovered combination
        return Finding(
            title=vh.hypothesis.title,
            observation=f"{vh.hypothesis.description}",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="No detailed analysis template available for this finding.",
            business_impact="Business impact could not be assessed automatically.",
            recommendation="Manual review recommended.",
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
    """Build a Finding for a composite hypothesis."""
    signal_key = frozenset(vh.hypothesis.supporting_signals)
    status = vh.status
    ctx = _build_context(vh)

    composite = _COMPOSITE_TEMPLATES.get(signal_key, {}).get(status)
    if composite is None:
        # Fallback
        return Finding(
            title=vh.hypothesis.title,
            observation=f"Combined signal pattern detected: {', '.join(s.value for s in vh.hypothesis.supporting_signals)}.",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="No detailed analysis template available for this composite finding.",
            business_impact="Business impact could not be assessed automatically.",
            recommendation="Manual review of combined signals recommended.",
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


def _build_finding(vh: ValidatedHypothesis) -> Finding:
    """Dispatch to simple or composite builder based on hypothesis type."""
    if vh.hypothesis.is_composite:
        return _build_composite_finding(vh)
    return _build_simple_finding(vh)


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
    refuted_ratio = len(refuted) / total if total > 0 else 0
    supported_ratio = len(supported) / total if total > 0 else 0

    if refuted_ratio > 0.3:
        overall_risk = "high"
    elif supported_ratio == 1.0 and len(refuted) == 0:
        overall_risk = "low"
    else:
        overall_risk = "medium"

    if supported_ratio > 0.5:
        overall_confidence = "high"
    elif supported_ratio > 0.2:
        overall_confidence = "medium"
    else:
        overall_confidence = "low"

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


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def generate_report(
    validation_report: ValidatedHypothesisReport,
    profile: DatasetProfile,
    dataset_summary: dict,
) -> InvestigationReport:
    """Generate a business-facing Investigation Report.

    Args:
        validation_report: Validated hypotheses with evidence classification.
        profile: Dataset profile with column metadata.
        dataset_summary: Output from analyze_dataframe().

    Returns:
        A structured InvestigationReport ready for analyst review or
        Phase 7 LLM narrative generation.
    """
    findings = [
        _build_finding(vh) for vh in validation_report.validated
    ]

    # Collect unique recommendations as next steps
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
    )
