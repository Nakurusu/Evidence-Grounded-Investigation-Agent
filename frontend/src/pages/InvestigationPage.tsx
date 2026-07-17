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
  type PipelineStage,
} from "@/hooks/useTaskPolling";
import { cn } from "@/lib/utils";

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
  evidence: "evidence",
  validation: "validation",
  report: "report",
  narrative: "narrative",
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

  const { task, isLoading, isError, isRunning, stage, elapsed } =
    useTaskPolling(taskId);

  const tabs = [
    { key: "overview", label: t.investigation.tabs.overview },
    { key: "findings", label: t.investigation.tabs.findings },
    { key: "narrative", label: t.investigation.tabs.narrative },
    { key: "interactive", label: t.investigation.tabs.interactive },
  ] as const;

  // Conditionally add cross-dataset tab (Phase 9)
  const hasGraph = !!task?.result?.investigation_graph;
  const allTabs = hasGraph
    ? [...tabs, { key: "cross" as const, label: "Cross-Dataset" }]
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
              <CrossDatasetTab graph={report.investigation_graph} />
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
  t,
}: {
  isProcessing: boolean;
  filename: string | undefined;
  stage: PipelineStage;
  elapsed: number;
  t: Translations;
}) {
  const stages = [
    "parsing",
    "profiling",
    "signals",
    "evidence",
    "validation",
    "report",
    "narrative",
  ] as const;

  const currentIdx = stages.indexOf(stage);

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

        <div className="space-y-0.5">
          {stages.map((s, i) => {
            const labelKey = STAGE_LABEL_KEYS[s];
            const label = t.investigation.loading.stages[labelKey];
            const isComplete = i < currentIdx;
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

        <p className="text-center text-xs text-muted">
          {formatElapsed(elapsed)} elapsed
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
  t,
}: {
  es: ExecutiveSummary;
  ds: DatasetSummary;
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
            label="Inconclusive"
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
            Overall confidence:{" "}
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
            { label: "Numeric", count: ds.numeric_columns.length, color: "bg-info-muted text-info" },
            { label: "Categorical", count: ds.categorical_columns.length, color: "bg-accent-muted text-accent" },
            { label: "Datetime", count: ds.datetime_columns.length, color: "bg-success-muted text-success" },
            { label: "Text", count: ds.text_columns.length, color: "bg-warning-muted text-warning" },
            { label: "Boolean", count: ds.boolean_columns.length, color: "bg-surface-elevated text-muted-foreground" },
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
                ? "All"
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
              {opt === "all" ? "All" : opt}
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
            Clear
          </button>
        )}
        <span className="ml-auto text-xs text-muted">
          {filtered.length} of {findings.length}
        </span>
      </div>

      {/* Finding cards */}
      {filtered.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No findings match the current filters.
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
  const hasDetail = f.analysis || f.business_impact || hasEvidence;

  return (
    <div className="rounded-lg border border-border bg-surface">
      {/* Header */}
      <div className="p-4 sm:p-5">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <StatusBadge status={f.status} t={t} />
          <ConfidenceBadge confidence={f.confidence} />
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
            {expanded ? "Less detail" : "More detail"}
          </button>
        )}
      </div>

      {/* Expandable detail */}
      {expanded && hasDetail && (
        <div className="animate-expand border-t border-border px-4 py-4 space-y-4 sm:px-5">
          {/* Analysis */}
          {f.analysis && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">Analysis</p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f.analysis}
              </p>
            </div>
          )}

          {/* Business impact */}
          {f.business_impact && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted">
                Business Impact
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {f.business_impact}
              </p>
            </div>
          )}

          {/* Evidence */}
          {f.supporting_evidence.length > 0 && (
            <EvidenceBlock
              label="Supporting Evidence"
              tone="success"
              evidence={f.supporting_evidence}
            />
          )}
          {f.contradicting_evidence.length > 0 && (
            <EvidenceBlock
              label="Contradicting Evidence"
              tone="danger"
              evidence={f.contradicting_evidence}
            />
          )}
        </div>
      )}
    </div>
  );
}

function EvidenceBlock({
  label,
  tone,
  evidence,
}: {
  label: string;
  tone: "success" | "danger";
  evidence: Evidence[];
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
                {e.metric}: {String(e.value)}
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
            Evidence Summary
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
}: {
  graph: InvestigationGraph;
}) {
  return (
    <div className="mx-auto max-w-3xl space-y-10">
      {/* Header */}
      <section>
        <h2 className="mb-2 text-lg font-semibold text-foreground">
          Cross-Dataset Analysis
        </h2>
        <p className="text-sm text-muted-foreground">
          Primary: <span className="font-medium text-foreground">{graph.primary_dataset}</span>
          {graph.secondary_datasets.length > 0 && (
            <>
              {" "}· Secondary:{" "}
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
            Shared Dimensions
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
            Relations ({graph.relations.length})
          </h2>
          <div className="space-y-4">
            {graph.relations.map((rel, i) => (
              <RelationCard key={i} rel={rel} />
            ))}
          </div>
        </section>
      )}

      {/* Cross Hypotheses */}
      {graph.cross_hypotheses.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            Cross-Dataset Hypotheses
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

function RelationCard({ rel }: { rel: CrossDatasetRelation }) {
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
        <ConfidenceBadge confidence={rel.confidence as HypothesisConfidence} />
      </div>
      <p className="text-sm text-foreground">{rel.description}</p>
      <div className="mt-2 space-y-1">
        <p className="text-xs text-muted">
          Primary:{" "}
          <span className="text-muted-foreground">{rel.primary_context}</span>
        </p>
        <p className="text-xs text-muted">
          Secondary:{" "}
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
}: {
  confidence: HypothesisConfidence | string;
}) {
  const colors: Record<string, string> = {
    high: "bg-success-muted text-success",
    medium: "bg-warning-muted text-warning",
    low: "bg-danger-muted text-danger",
  };
  const color =
    colors[confidence.toLowerCase()] ?? "bg-surface-elevated text-muted";

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        color,
      )}
    >
      {confidence}
    </span>
  );
}
