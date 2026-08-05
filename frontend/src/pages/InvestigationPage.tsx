import { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import type {
  AIInvestigationReport,
  ExecutiveSummary,
  DatasetSummary,
  Finding,
  Narrative,
  ModelMetadata,
  InvestigationGraph,
  CrossDatasetRelation,
  Evidence,
  QualitySummary,
} from "@/api/types";
import type { HypothesisStatus, HypothesisConfidence } from "@/api/types";
import {
  AlertTriangle,
  ChevronRight,
  Check,
  FileText,
  ChevronDown,
  Filter,
  X,
  ArrowRight,
  Link2,
  TrendingUp,
  TrendingDown,
  GitBranch,
} from "lucide-react";
import { useT } from "@/i18n/LanguageProvider";
import type { Translations } from "@/i18n/translations";
import {
  useTaskPolling,
  formatElapsed,
  PIPELINE_STAGES,
  type PipelineStage,
} from "@/hooks/useTaskPolling";
import { cn } from "@/lib/utils";
import { formatMetricValue, metricLabel } from "@/lib/metrics";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const STAGE_LABEL_KEYS: Record<
  PipelineStage,
  keyof Translations["investigation"]["loading"]["stages"]
> = {
  parsing: "parsing",
  profiling: "profiling",
  signals: "signals",
  questions: "questions",
  hypotheses: "hypotheses",
  evidence: "evidence",
  validation: "validation",
  report: "report",
  narrative: "narrative",
  interactive: "interactive",
  secondary_profiling: "secondary_profiling",
  cross_dataset: "cross_dataset",
  completed: "completed",
};

const STATUS_OPTIONS: ("all" | HypothesisStatus)[] = [
  "all",
  "supported",
  "refuted",
  "inconclusive",
];
const CONFIDENCE_OPTIONS: ("all" | HypothesisConfidence)[] = [
  "all",
  "high",
  "medium",
  "low",
];

/* ================================================================== */
/*  Page                                                                */
/* ================================================================== */

export function InvestigationPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") ?? "overview";
  const t = useT();

  const {
    task,
    isLoading,
    isError,
    isRunning,
    stage,
    elapsed,
    progressPercent,
    completedStages,
    stageDetail,
    failedStage,
    stageTitle,
    stageGoal,
    stageInput,
    stageOutput,
    stageReason,
  } = useTaskPolling(taskId);

  const tabs = [
    { key: "overview", label: t.investigation.tabs.overview },
    { key: "findings", label: t.investigation.tabs.findings },
    { key: "narrative", label: t.investigation.tabs.narrative },
    { key: "interactive", label: t.investigation.tabs.interactive },
  ] as const;

  // Conditionally add cross-dataset tab (Phase 9)
  const hasGraph = !!task?.result?.investigation_graph;
  const allTabs = hasGraph
    ? [...tabs, { key: "cross" as const, label: t.investigation.crossDataset.tab }]
    : tabs;

  const setTab = (tab: string) => {
    setSearchParams({ tab });
  };

  // --- Loading / processing -----------------------------------------------
  if (isLoading || isRunning) {
    return (
      <ProcessingView
        isProcessing={task?.status === "processing"}
        filename={task?.filename}
        stage={stage}
        elapsed={elapsed}
        progressPercent={progressPercent}
        completedStages={completedStages}
        stageDetail={stageDetail}
        failedStage={failedStage}
        stageTitle={stageTitle}
        stageGoal={stageGoal}
        stageInput={stageInput}
        stageOutput={stageOutput}
        stageReason={stageReason}
        t={t}
      />
    );
  }

  // --- Error --------------------------------------------------------------
  if (isError || task?.status === "failed") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-16 sm:px-6 sm:py-24">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger-muted">
          <AlertTriangle className="h-6 w-6 text-danger" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">
          {t.investigation.error.title}
        </h2>
        <p className="max-w-md text-center text-sm text-muted-foreground">
          {task?.error_message ?? t.investigation.error.default}
        </p>
      </div>
    );
  }

  // --- Completed ----------------------------------------------------------
  const report = task?.result;

  return (
    <div className="flex flex-1 flex-col">
      {/* Tab bar — scrollable on mobile */}
      <div className="border-b border-border">
        <nav
          className="flex gap-0 overflow-x-auto px-4 sm:px-6 tab-scroll"
          role="tablist"
        >
          {allTabs.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => setTab(tab.key)}
              className={cn(
                "relative shrink-0 px-3 py-3 text-sm font-medium transition-colors sm:px-4",
                activeTab === tab.key
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {tab.label}
              {activeTab === tab.key && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="flex-1 px-4 py-6 sm:px-6 sm:py-8 animate-fade-in" key={activeTab}>
        {report && (
          <>
            {activeTab === "overview" && (
              <OverviewTab
                es={report.investigation_report.executive_summary}
                ds={report.investigation_report.dataset_summary}
                quality={report.investigation_report.quality_summary}
                t={t}
              />
            )}
            {activeTab === "findings" && (
              <FindingsTab
                findings={report.investigation_report.findings}
                t={t}
              />
            )}
            {activeTab === "narrative" && (
              <NarrativeTab
                narrative={report.narrative}
                meta={report.model_metadata}
                t={t}
              />
            )}
            {activeTab === "interactive" && (
              <InteractiveTab
                report={report}
                t={t}
              />
            )}
            {activeTab === "cross" && report.investigation_graph && (
              <CrossDatasetTab graph={report.investigation_graph} t={t} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Processing view                                                    */
/* ================================================================== */

function ProcessingView({
  isProcessing,
  filename,
  stage,
  elapsed,
  progressPercent,
  completedStages,
  stageDetail,
  failedStage,
  stageTitle,
  stageGoal,
  stageInput,
  stageOutput,
  stageReason,
  t,
}: {
  isProcessing: boolean;
  filename: string | undefined;
  stage: PipelineStage;
  elapsed: number;
  progressPercent: number | null;
  completedStages: string[];
  stageDetail: string | null;
  failedStage: string | null;
  stageTitle: string | null;
  stageGoal: string | null;
  stageInput: string | null;
  stageOutput: string | null;
  stageReason: string | null;
  t: Translations;
}) {
  const stages = PIPELINE_STAGES;
  const currentIdx = stages.indexOf(stage);
  const safeCurrentIdx = currentIdx >= 0 ? currentIdx : 0;
  const safeProgress = progressPercent ?? Math.max(5, (safeCurrentIdx + 1) * 8);
  const fallbackStageLabel =
    t.investigation.loading.stages[STAGE_LABEL_KEYS[stage] ?? "parsing"];
  const displayTitle = stageTitle ?? fallbackStageLabel;

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-16 sm:px-6 sm:py-24">
      <div className="w-full max-w-md space-y-6 sm:space-y-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-accent-muted">
            <FileText className="h-6 w-6 text-accent" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">
            {isProcessing
              ? t.investigation.loading.processing
              : t.investigation.loading.starting}
          </h2>
          {filename && <p className="mt-1 text-sm text-muted">{filename}</p>}
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs font-medium text-muted">
            {t.investigation.loading.currentStage}
          </p>
          <h3 className="mt-1 text-sm font-semibold text-foreground">
            {displayTitle}
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {stageGoal ?? stageDetail ?? t.investigation.loading.fallbackDetail}
          </p>
          <div className="mt-3 grid gap-2 text-xs text-muted sm:grid-cols-2">
            {stageInput && (
              <p>
                <span className="font-medium text-muted-foreground">
                  {t.investigation.loading.stageInput}:
                </span>{" "}
                {stageInput}
              </p>
            )}
            {stageOutput && (
              <p>
                <span className="font-medium text-muted-foreground">
                  {t.investigation.loading.stageOutput}:
                </span>{" "}
                {stageOutput}
              </p>
            )}
          </div>
          {stageReason && (
            <p className="mt-3 text-xs leading-relaxed text-muted">
              <span className="font-medium text-muted-foreground">
                {t.investigation.loading.stageReason}:
              </span>{" "}
              {stageReason}
            </p>
          )}
        </div>

        <div className="space-y-0.5">
          {stages.map((s, i) => {
            const labelKey = STAGE_LABEL_KEYS[s];
            const label = t.investigation.loading.stages[labelKey];
            const isComplete = completedStages.includes(s) || i < currentIdx;
            const isCurrent = i === currentIdx;
            const isPending = i > currentIdx;

            return (
              <div
                key={s}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 transition-colors",
                  isCurrent && "bg-accent-muted",
                )}
              >
                <div className="flex h-5 w-5 shrink-0 items-center justify-center">
                  {isComplete ? (
                    <Check className="h-4 w-4 text-success" />
                  ) : isCurrent ? (
                    <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
                  ) : (
                    <div className="h-2 w-2 rounded-full bg-border" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-sm",
                    isPending
                      ? "text-muted"
                      : isCurrent
                        ? "font-medium text-foreground"
                        : "text-muted-foreground",
                  )}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        <div className="space-y-2 rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              {stageDetail ?? t.investigation.loading.fallbackDetail}
            </span>
            <span>{safeProgress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-surface-elevated">
            <div
              className="h-full rounded-full bg-accent transition-all"
              style={{ width: `${Math.min(100, Math.max(0, safeProgress))}%` }}
            />
          </div>
          <div className="flex flex-wrap justify-between gap-2 text-xs text-muted">
            <span>
              {t.investigation.loading.completedCount(
                completedStages.length,
                stages.length,
              )}
            </span>
            {failedStage && <span>{failedStage}</span>}
          </div>
        </div>

        <p className="text-center text-xs text-muted">
          {t.investigation.loading.elapsed(formatElapsed(elapsed))}
        </p>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Overview tab                                                       */
/* ================================================================== */

function OverviewTab({
  es,
  ds,
  quality,
  t,
}: {
  es: ExecutiveSummary;
  ds: DatasetSummary;
  quality: QualitySummary | null;
  t: Translations;
}) {
  return (
    <div className="mx-auto max-w-3xl space-y-10">
      {/* Stat cards */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          {t.investigation.overview.executiveSummary}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard
            label={t.investigation.overview.hypotheses}
            value={String(es.total_hypotheses)}
          />
          <StatCard
            label={t.investigation.overview.supported}
            value={String(es.supported_count)}
            tone="success"
          />
          <StatCard
            label={t.investigation.overview.refuted}
            value={String(es.refuted_count)}
            tone="danger"
          />
          <StatCard
            label={t.investigation.overview.inconclusive}
            value={String(es.inconclusive_count)}
            tone="warning"
          />
          <StatCard
            label={t.investigation.overview.riskLevel}
            value={es.overall_risk}
          />
        </div>

        {/* Confidence & risk */}
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <span className="text-muted-foreground">
            {t.investigation.overview.confidence}:{" "}
            <span className="font-medium text-foreground">
              {es.overall_confidence}
            </span>
          </span>
        </div>

        {/* Highest priority findings */}
        {es.highest_priority_findings.length > 0 && (
          <div className="mt-4 space-y-1.5">
            <p className="text-xs font-medium text-muted">
              {t.investigation.overview.highestPriority}
            </p>
            {es.highest_priority_findings.map((f, i) => (
              <p key={i} className="text-sm text-muted-foreground">
                {f}
              </p>
            ))}
          </div>
        )}
      </section>

      {/* Dataset */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          {t.investigation.overview.dataset}
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {t.investigation.overview.rowsColumns(ds.row_count, ds.column_count)}
        </p>

        {/* Column type breakdown */}
        <div className="flex flex-wrap gap-2">
          {[
            { label: t.investigation.overview.columnTypes.numeric, count: ds.numeric_columns.length, color: "bg-info-muted text-info" },
            { label: t.investigation.overview.columnTypes.categorical, count: ds.categorical_columns.length, color: "bg-accent-muted text-accent" },
            { label: t.investigation.overview.columnTypes.datetime, count: ds.datetime_columns.length, color: "bg-success-muted text-success" },
            { label: t.investigation.overview.columnTypes.text, count: ds.text_columns.length, color: "bg-warning-muted text-warning" },
            { label: t.investigation.overview.columnTypes.boolean, count: ds.boolean_columns.length, color: "bg-surface-elevated text-muted-foreground" },
          ]
            .filter((c) => c.count > 0)
            .map((c) => (
              <span
                key={c.label}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                  c.color,
                )}
              >
                {c.label}
                <span className="opacity-70">{c.count}</span>
              </span>
            ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          {t.investigation.overview.quality}
        </h2>
        <div className="rounded-lg border border-border bg-surface p-4">
          {quality && quality.warnings.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-foreground">
                {t.investigation.overview.qualityRisk}: {quality.risk_level}
              </p>
              <ul className="space-y-2">
                {quality.warnings.map((warning, i) => (
                  <li key={i} className="text-sm text-muted-foreground">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t.investigation.overview.noQualityIssues}
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

/* ================================================================== */
/*  Findings tab                                                       */
/* ================================================================== */

function FindingsTab({ findings, t }: { findings: Finding[]; t: Translations }) {
  const [statusFilter, setStatusFilter] = useState<"all" | HypothesisStatus>("all");
  const [confidenceFilter, setConfidenceFilter] = useState<
    "all" | HypothesisConfidence
  >("all");

  const filtered = findings.filter((f) => {
    if (statusFilter !== "all" && f.status !== statusFilter) return false;
    if (confidenceFilter !== "all" && f.confidence !== confidenceFilter)
      return false;
    return true;
  });

  const activeFilters =
    statusFilter !== "all" || confidenceFilter !== "all";

  if (findings.length === 0) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center">
        <p className="text-sm text-muted-foreground">
          {t.investigation.findings.empty}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Filter bar — wraps naturally on mobile */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <Filter className="h-4 w-4 text-muted" />
        {/* Status filter */}
        <div className="flex gap-1 rounded-md border border-border bg-surface p-0.5">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setStatusFilter(opt)}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                statusFilter === opt
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {opt === "all"
                ? t.investigation.findings.all
                : t.investigation.status[opt as keyof typeof t.investigation.status]}
            </button>
          ))}
        </div>
        {/* Confidence filter */}
        <div className="flex gap-1 rounded-md border border-border bg-surface p-0.5">
          {CONFIDENCE_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setConfidenceFilter(opt)}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                confidenceFilter === opt
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {opt === "all"
                ? t.investigation.findings.all
                : t.investigation.confidence[opt]}
            </button>
          ))}
        </div>
        {activeFilters && (
          <button
            onClick={() => {
              setStatusFilter("all");
              setConfidenceFilter("all");
            }}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-3 w-3" />
            {t.investigation.findings.clear}
          </button>
        )}
        <span className="ml-auto text-xs text-muted">
          {t.investigation.findings.count(filtered.length, findings.length)}
        </span>
      </div>

      {/* Finding cards */}
      {filtered.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          {t.investigation.findings.noFilterMatch}
        </p>
      ) : (
        <div className="space-y-4">
          {filtered.map((f, i) => (
            <FindingCard key={i} finding={f} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function FindingCard({ finding: f, t }: { finding: Finding; t: Translations }) {
  const [expanded, setExpanded] = useState(false);
  const hasEvidence =
    f.supporting_evidence.length > 0 || f.contradicting_evidence.length > 0;
  const hasMetrics = Object.keys(f.key_metrics ?? {}).length > 0;
  const hasTrace = Object.keys(f.trace ?? {}).length > 0;
  const hasDetail =
    f.analysis ||
    f.business_impact ||
    hasEvidence ||
    f.affected_columns.length > 0 ||
    hasMetrics ||
    hasTrace ||
    !!f.evidence_strength ||
    f.uncertainty_notes.length > 0;

  return (
    <div className="rounded-lg border border-border bg-surface">
      {/* Header */}
      <div className="p-4 sm:p-5">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <StatusBadge status={f.status} t={t} />
          <ConfidenceBadge confidence={f.confidence} t={t} />
        </div>
        <h3 className="mb-2 text-sm font-semibold text-foreground">
          {f.title}
        </h3>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {f.observation}
        </p>

        {/* Recommendation (always visible) */}
        {f.recommendation && (
          <div className="mt-3 flex items-start gap-2 rounded-md bg-accent-muted p-3">
            <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <p className="text-sm text-foreground">{f.recommendation}</p>
          </div>
        )}

        {/* Expand toggle */}
        {hasDetail && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 transition-transform",
                expanded && "rotate-180",
              )}
            />
            {expanded
              ? t.investigation.findings.lessDetail
              : t.investigation.findings.moreDetail}
          </button>
        )}
      </div>

      {/* Expandable detail */}
      {expanded && hasDetail && (
        <div className="animate-expand border-t border-border px-4 py-4 space-y-4 sm:px-5">
          {/* Analysis */}
          {f.analysis && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">
                {t.investigation.findings.analysis}
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f.analysis}
              </p>
            </div>
          )}

          {/* Business impact */}
          {f.business_impact && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">
                {t.investigation.findings.businessImpact}
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f.business_impact}
              </p>
            </div>
          )}

          {f.evidence_strength && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">
                {t.investigation.findings.evidenceStrength}
              </p>
              <p className="text-sm text-muted-foreground">
                {f.evidence_strength}
              </p>
            </div>
          )}

          {f.uncertainty_notes.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">
                {t.investigation.findings.uncertaintyNotes}
              </p>
              <ul className="space-y-1">
                {f.uncertainty_notes.map((note, i) => (
                  <li key={i} className="text-sm text-muted-foreground">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {f.affected_columns.length > 0 && (
            <TagList
              label={t.investigation.findings.affectedColumns}
              values={f.affected_columns}
            />
          )}

          {hasMetrics && (
            <MetricGrid
              label={t.investigation.findings.keyMetrics}
              metrics={f.key_metrics}
            />
          )}

          {hasTrace && (
            <TraceBlock
              label={t.investigation.findings.evidenceTrace}
              trace={f.trace}
            />
          )}

          {/* Evidence */}
          {f.supporting_evidence.length > 0 && (
            <EvidenceBlock
              label={t.investigation.findings.supportingEvidence}
              tone="success"
              evidence={f.supporting_evidence}
              t={t}
            />
          )}
          {f.contradicting_evidence.length > 0 && (
            <EvidenceBlock
              label={t.investigation.findings.contradictingEvidence}
              tone="danger"
              evidence={f.contradicting_evidence}
              t={t}
            />
          )}
        </div>
      )}
    </div>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted">{label}</p>
      <div className="flex flex-wrap gap-2">
        {values.map((value) => (
          <span
            key={value}
            className="rounded-full bg-surface-elevated px-2.5 py-0.5 text-xs text-muted-foreground"
          >
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function MetricGrid({
  label,
  metrics,
}: {
  label: string;
  metrics: Record<string, string | number>;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted">{label}</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {Object.entries(metrics).map(([key, value]) => (
          <div
            key={key}
            className="rounded-md border border-border bg-surface-elevated px-3 py-2"
          >
            <p className="text-xs text-muted">{metricLabel(key)}</p>
            <p className="mt-0.5 font-mono text-sm text-foreground">
              {formatMetricValue(key, value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TraceBlock({
  label,
  trace,
}: {
  label: string;
  trace: Record<string, string | string[]>;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted">{label}</p>
      <div className="space-y-2 rounded-md border border-border bg-surface-elevated p-3">
        {Object.entries(trace).map(([key, value]) => (
          <div key={key} className="text-xs">
            <span className="font-medium text-muted-foreground">{key}: </span>
            <span className="text-muted">
              {Array.isArray(value) ? value.join("、") : value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceBlock({
  label,
  tone,
  evidence,
  t,
}: {
  label: string;
  tone: "success" | "danger";
  evidence: Evidence[];
  t: Translations;
}) {
  const color =
    tone === "success"
      ? "border-l-success bg-success-muted/50"
      : "border-l-danger bg-danger-muted/50";

  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted">{label}</p>
      <div className="space-y-2">
        {evidence.map((e, i) => (
          <div
            key={i}
            className={cn(
              "rounded-r-md border-l-2 px-3 py-2 text-sm",
              color,
            )}
          >
            <p className="font-medium text-foreground">{e.title}</p>
            {e.description && (
              <p className="mt-0.5 text-muted-foreground">{e.description}</p>
            )}
            {e.metric && e.value !== null && (
              <p className="mt-1 font-mono text-xs text-muted">
                {metricLabel(e.metric, e.display_label)}:{" "}
                {formatMetricValue(e.metric, e.value, e.display_format)}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
              {e.method && (
                <span>
                  {t.investigation.findings.method}: {e.method}
                </span>
              )}
              {e.threshold !== null && e.threshold !== undefined && (
                <span>
                  {t.investigation.findings.threshold}: {String(e.threshold)}
                </span>
              )}
              {e.sample_size !== null && e.sample_size !== undefined && (
                <span>
                  {t.investigation.findings.sampleSize}: {e.sample_size}
                </span>
              )}
            </div>
            {e.limitation && (
              <p className="mt-1 text-xs text-muted">
                {t.investigation.findings.limitation}: {e.limitation}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Narrative tab                                                      */
/* ================================================================== */

function NarrativeTab({
  narrative,
  meta,
  t,
}: {
  narrative: Narrative | null;
  meta: ModelMetadata | null;
  t: Translations;
}) {
  if (!narrative) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center">
        <p className="text-sm text-muted-foreground">
          {t.investigation.narrative.empty}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-10">
      {narrative.plain_language_summary && (
        <section className="rounded-lg border border-accent/20 bg-accent-muted p-4">
          <h2 className="mb-3 text-lg font-semibold text-foreground">
            {t.investigation.narrative.plainLanguageSummary}
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {narrative.plain_language_summary}
          </p>
        </section>
      )}

      <NarrativeListSection
        title={t.investigation.narrative.whatHappened}
        items={narrative.what_happened}
      />
      <NarrativeListSection
        title={t.investigation.narrative.whyItMatters}
        items={narrative.why_it_matters}
      />
      <NarrativeListSection
        title={t.investigation.narrative.whatToCheckNext}
        items={narrative.what_to_check_next}
      />
      <NarrativeListSection
        title={t.investigation.narrative.confidenceNotes}
        items={narrative.confidence_notes}
      />

      {/* Executive Summary — lead paragraph */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-foreground">
          {t.investigation.narrative.executiveSummary}
        </h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {narrative.executive_summary}
        </p>
      </section>

      {/* Key Findings — prose list */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          {t.investigation.narrative.keyFindings}
        </h2>
        <div className="space-y-4">
          {narrative.key_findings.map((f, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-muted text-xs font-medium text-accent">
                {i + 1}
              </span>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Evidence summary */}
      {narrative.supporting_evidence_summary && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-foreground">
            {t.investigation.narrative.evidenceSummary}
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {narrative.supporting_evidence_summary}
          </p>
        </section>
      )}

      {/* Business Impact — callout style */}
      {narrative.business_impact_summary && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-foreground">
            {t.investigation.narrative.businessImpact}
          </h2>
          <div className="rounded-lg border border-accent/20 bg-accent-muted p-4">
            <p className="text-sm leading-relaxed text-muted-foreground">
              {narrative.business_impact_summary}
            </p>
          </div>
        </section>
      )}

      {/* Recommendations — numbered list */}
      {narrative.recommendations.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t.investigation.narrative.recommendations}
          </h2>
          <div className="space-y-3">
            {narrative.recommendations.map((r, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-muted text-xs font-medium text-accent">
                  {i + 1}
                </span>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {r}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Model metadata — subtle footer */}
      {meta && (
        <div className="border-t border-border pt-4">
          <p className="text-xs text-muted">
            {t.investigation.narrative.generatedBy(
              meta.provider,
              meta.model_name,
              meta.prompt_version,
            )}
          </p>
        </div>
      )}
    </div>
  );
}

function NarrativeListSection({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;
  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-foreground">{title}</h2>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-muted text-xs font-medium text-accent">
              {i + 1}
            </span>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {item}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ================================================================== */
/*  Interactive tab                                                    */
/* ================================================================== */

function InteractiveTab({
  report,
  t,
}: {
  report: AIInvestigationReport;
  t: Translations;
}) {
  const interactive = report.interactive_investigation;

  if (!interactive) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center">
        <p className="text-sm text-muted-foreground">
          {t.investigation.interactive.empty}
        </p>
      </div>
    );
  }

  const {
    follow_up_questions: questions,
    data_gaps: gaps,
    investigation_paths: paths,
    unresolved_areas: unresolved,
  } = interactive;

  return (
    <div className="mx-auto max-w-3xl space-y-12">
      {/* Follow-up Questions */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          {t.investigation.interactive.followUp}
        </h2>
        <div className="space-y-3">
          {questions.map((q, i) => (
            <div
              key={i}
              className="rounded-lg border border-border bg-surface p-4"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                    q.priority === "high"
                      ? "bg-danger-muted text-danger"
                      : q.priority === "medium"
                        ? "bg-warning-muted text-warning"
                        : "bg-surface-elevated text-muted-foreground",
                  )}
                >
                  {q.priority.toUpperCase()}
                </span>
                <span className="text-xs text-muted">{q.category}</span>
              </div>
              <p className="mb-2 text-sm text-foreground">{q.question}</p>

              {/* Related findings */}
              {q.related_finding_titles.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <Link2 className="h-3 w-3 text-muted" />
                  {q.related_finding_titles.map((title, j) => (
                    <span
                      key={j}
                      className="inline-flex rounded bg-accent-muted px-1.5 py-0.5 text-xs text-accent"
                    >
                      {title}
                    </span>
                  ))}
                </div>
              )}

              {/* Required data */}
              {q.required_data.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {q.required_data.map((d, j) => (
                    <span
                      key={j}
                      className="inline-flex rounded bg-surface-elevated px-1.5 py-0.5 text-xs text-muted"
                    >
                      {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Unresolved Areas */}
      {unresolved.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            Unresolved Areas
          </h2>
          <div className="space-y-2">
            {unresolved.map((area, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-md bg-warning-muted p-3"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                <p className="text-sm text-foreground">{area}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Data Gaps */}
      {gaps.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t.investigation.interactive.dataGaps}
          </h2>
          <div className="space-y-3">
            {gaps.map((g, i) => (
              <div
                key={i}
                className="rounded-lg border border-border bg-surface p-4"
              >
                <p className="mb-1 text-sm font-medium text-foreground">
                  {g.gap}
                </p>
                <p className="text-sm text-muted-foreground">{g.impact}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted">
                    {t.investigation.interactive.source}: {g.suggested_source}
                  </span>
                  {g.affected_hypotheses.length > 0 && (
                    <span className="text-xs text-muted">
                      · Affects: {g.affected_hypotheses.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Investigation Paths */}
      {paths.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t.investigation.interactive.paths}
          </h2>
          <div className="space-y-4">
            {paths.map((p, i) => (
              <div
                key={i}
                className="rounded-lg border border-border bg-surface p-4"
              >
                <div className="mb-1 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-accent" />
                  <h3 className="text-sm font-semibold text-foreground">
                    {p.title}
                  </h3>
                </div>
                <p className="mb-3 text-sm text-muted-foreground">
                  {p.description}
                </p>
                <div className="space-y-2">
                  {p.steps.map((s, j) => (
                    <div key={j} className="flex items-start gap-3">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent-muted text-xs font-medium text-accent">
                        {j + 1}
                      </span>
                      <p className="text-sm text-muted-foreground">{s}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* ================================================================== */
/*  Cross-Dataset tab (Phase 9)                                        */
/* ================================================================== */

function CrossDatasetTab({
  graph,
  t,
}: {
  graph: InvestigationGraph;
  t: Translations;
}) {
  return (
    <div className="mx-auto max-w-3xl space-y-10">
      {/* Header */}
      <section>
        <h2 className="mb-2 text-lg font-semibold text-foreground">
          {t.investigation.crossDataset.title}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t.investigation.crossDataset.primary}: <span className="font-medium text-foreground">{graph.primary_dataset}</span>
          {graph.secondary_datasets.length > 0 && (
            <>
              {" "}· {t.investigation.crossDataset.secondary}:{" "}
              <span className="font-medium text-foreground">
                {graph.secondary_datasets.join(", ")}
              </span>
            </>
          )}
        </p>
      </section>

      {/* Shared Dimensions */}
      {graph.shared_dimensions.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-foreground">
            {t.investigation.crossDataset.sharedDimensions}
          </h2>
          <div className="flex flex-wrap gap-2">
            {graph.shared_dimensions.map((dim) => (
              <span
                key={dim}
                className="inline-flex items-center gap-1.5 rounded-full bg-accent-muted px-2.5 py-0.5 text-xs font-medium text-accent"
              >
                <Link2 className="h-3 w-3" />
                {dim}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Relations */}
      {graph.relations.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t.investigation.crossDataset.relations(graph.relations.length)}
          </h2>
          <div className="space-y-4">
            {graph.relations.map((rel, i) => (
              <RelationCard key={i} rel={rel} t={t} />
            ))}
          </div>
        </section>
      )}

      {/* Cross Hypotheses */}
      {graph.cross_hypotheses.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            {t.investigation.crossDataset.hypotheses}
          </h2>
          <div className="space-y-2">
            {graph.cross_hypotheses.map((h, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-md bg-surface-elevated p-3"
              >
                <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <p className="text-sm text-muted-foreground">{h}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function RelationCard({
  rel,
  t,
}: {
  rel: CrossDatasetRelation;
  t: Translations;
}) {
  const typeIcons: Record<string, React.ReactNode> = {
    correlated_trend: <TrendingUp className="h-4 w-4 text-success" />,
    opposite_trend: <TrendingDown className="h-4 w-4 text-danger" />,
    shared_dimension: <Link2 className="h-4 w-4 text-accent" />,
    complementary_signal: <GitBranch className="h-4 w-4 text-info" />,
  };

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-2 flex items-center gap-2">
        {typeIcons[rel.type] ?? <Link2 className="h-4 w-4 text-muted" />}
        <span className="text-xs font-medium text-muted uppercase">
          {rel.type}
        </span>
        <ConfidenceBadge
          confidence={rel.confidence as HypothesisConfidence}
          t={t}
        />
      </div>
      <p className="text-sm text-foreground">{rel.description}</p>
      <div className="mt-2 space-y-1">
        <p className="text-xs text-muted">
          {t.investigation.crossDataset.primary}:{" "}
          <span className="text-muted-foreground">{rel.primary_context}</span>
        </p>
        <p className="text-xs text-muted">
          {t.investigation.crossDataset.secondary}:{" "}
          <span className="text-muted-foreground">
            {rel.secondary_context}
          </span>
        </p>
      </div>
      {rel.shared_columns.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {rel.shared_columns.map((col) => (
            <span
              key={col}
              className="inline-flex rounded bg-accent-muted px-1.5 py-0.5 text-xs text-accent"
            >
              {col}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ================================================================== */
/*  Shared mini-components                                             */
/* ================================================================== */

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "success" | "danger" | "warning";
}) {
  const color =
    tone === "success"
      ? "text-success"
      : tone === "danger"
        ? "text-danger"
        : tone === "warning"
          ? "text-warning"
          : "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="mb-1 text-xs text-muted">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function StatusBadge({ status, t }: { status: string; t: Translations }) {
  const labels: Record<string, string> = {
    supported: t.investigation.status.supported,
    refuted: t.investigation.status.refuted,
    inconclusive: t.investigation.status.inconclusive,
  };
  const colors: Record<string, string> = {
    supported: "bg-success-muted text-success",
    refuted: "bg-danger-muted text-danger",
    inconclusive: "bg-warning-muted text-warning",
  };
  const color =
    colors[status.toLowerCase()] ?? "bg-surface-elevated text-muted";
  const label = labels[status.toLowerCase()] ?? status;

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        color,
      )}
    >
      {label}
    </span>
  );
}

function ConfidenceBadge({
  confidence,
  t,
}: {
  confidence: HypothesisConfidence | string;
  t: Translations;
}) {
  const colors: Record<string, string> = {
    high: "bg-success-muted text-success",
    medium: "bg-warning-muted text-warning",
    low: "bg-danger-muted text-danger",
  };
  const color =
    colors[confidence.toLowerCase()] ?? "bg-surface-elevated text-muted";
  const label =
    t.investigation.confidence[
      confidence.toLowerCase() as keyof typeof t.investigation.confidence
    ] ?? confidence;

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        color,
      )}
    >
      {label}
    </span>
  );
}
