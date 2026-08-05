/* ------------------------------------------------------------------ */
/*  TypeScript types mirroring the backend Pydantic schemas.          */
/*  These are the source-of-truth contracts between frontend & API.   */
/* ------------------------------------------------------------------ */

// -- Enums ----------------------------------------------------------------

export type TaskStatus = "pending" | "processing" | "completed" | "failed";

export type SignalType =
  | "high_missing_rate"
  | "high_cardinality"
  | "outlier_detected"
  | "increasing_trend"
  | "decreasing_trend"
  | "high_concentration"
  | "right_skewed"
  | "left_skewed"
  | "low_variance";

export type SignalSeverity = "info" | "warning" | "high";

export type HypothesisStatus = "supported" | "refuted" | "inconclusive";

export type HypothesisConfidence = "high" | "medium" | "low";

export type ColumnType = "numeric" | "categorical" | "datetime" | "boolean" | "text";

export type ColumnSemanticRole =
  | "metric"
  | "dimension"
  | "time"
  | "entity"
  | "identifier";

// -- Task ------------------------------------------------------------------

export interface TaskProgress {
  current_stage: string | null;
  completed_stages: string[];
  percent: number | null;
  stage_detail: string | null;
  failed_stage: string | null;
  stage_title: string | null;
  stage_goal: string | null;
  stage_input: string | null;
  stage_output: string | null;
  stage_reason: string | null;
}

export interface TaskResponse {
  id: string;
  status: TaskStatus;
  filename: string;
  investigation_question: string | null;
  created_at: string;
  finished_at: string | null;
  result: AIInvestigationReport | null;
  error_message: string | null;
  current_stage: string | null;
  progress: TaskProgress | null;
}

// -- Investigation Report --------------------------------------------------

export interface ExecutiveSummary {
  investigation_question: string | null;
  total_hypotheses: number;
  supported_count: number;
  refuted_count: number;
  inconclusive_count: number;
  highest_priority_findings: string[];
  overall_risk: string;
  overall_confidence: string;
}

export interface DatasetSummary {
  row_count: number;
  column_count: number;
  numeric_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  text_columns: string[];
  boolean_columns: string[];
  metric_columns: string[];
  dimension_columns: string[];
  time_columns: string[];
  entity_columns: string[];
  identifier_columns: string[];
}

export interface Evidence {
  title: string;
  description: string;
  metric: string | null;
  value: string | number | null;
  supporting_signal: SignalType | null;
  related_column: string | null;
  method: string | null;
  threshold: string | number | null;
  sample_size: number | null;
  direction: string | null;
  strength: string | null;
  limitation: string | null;
  display_label: string | null;
  display_format: string | null;
}

export interface Finding {
  title: string;
  observation: string;
  status: HypothesisStatus;
  confidence: HypothesisConfidence;
  supporting_evidence: Evidence[];
  contradicting_evidence: Evidence[];
  analysis: string;
  business_impact: string;
  recommendation: string;
  primary_signal_type: string | null;
  affected_columns: string[];
  key_metrics: Record<string, string | number>;
  trace: Record<string, string | string[]>;
  evidence_strength: string | null;
  uncertainty_notes: string[];
}

export interface CauseCandidate {
  title: string;
  explanation: string;
  score: number;
  confidence: HypothesisConfidence;
  related_columns: string[];
  supporting_finding_titles: string[];
  supporting_evidence_titles: string[];
  limitations: string[];
  next_validation_step: string;
}

export interface QualitySummary {
  issue_count: number;
  risk_level: string;
  warnings: string[];
}

export interface InvestigationReport {
  executive_summary: ExecutiveSummary;
  dataset_summary: DatasetSummary;
  findings: Finding[];
  cause_candidates: CauseCandidate[];
  next_steps: string[];
  quality_summary: QualitySummary | null;
}

// -- Narrative -------------------------------------------------------------

export interface Narrative {
  executive_summary: string;
  key_findings: string[];
  supporting_evidence_summary: string;
  business_impact_summary: string;
  recommendations: string[];
  plain_language_summary: string | null;
  what_happened: string[];
  why_it_matters: string[];
  what_to_check_next: string[];
  confidence_notes: string[];
}

export interface ModelMetadata {
  provider: string;
  model_name: string;
  prompt_version: string;
  generated_at: string;
}

// -- Interactive Investigation ---------------------------------------------

export interface FollowUpQuestion {
  question: string;
  priority: string;
  category: string;
  related_finding_titles: string[];
  required_data: string[];
}

export interface DrillDownEvidence {
  label: string;
  value: string | number | null;
  description: string;
}

export interface DrillDownResult {
  step_id: string;
  question: string;
  status: string;
  analysis_type: string;
  summary: string;
  related_columns: string[];
  evidence: DrillDownEvidence[];
  sample_records: Record<string, string | number | boolean | null>[];
  limitations: string[];
  generated_at: string;
}

export interface DataGap {
  gap: string;
  impact: string;
  affected_hypotheses: string[];
  suggested_source: string;
}

export interface InvestigationPath {
  title: string;
  description: string;
  steps: string[];
  starting_finding: string;
}

export interface InteractiveInvestigationReport {
  follow_up_questions: FollowUpQuestion[];
  data_gaps: DataGap[];
  investigation_paths: InvestigationPath[];
  unresolved_areas: string[];
  drilldown_steps: DrillDownResult[];
}

// -- Cross-Dataset (Phase 9) -----------------------------------------------

export interface CrossDatasetRelation {
  type: string;
  description: string;
  primary_context: string;
  secondary_context: string;
  shared_columns: string[];
  confidence: string;
}

export interface InvestigationGraph {
  primary_dataset: string;
  secondary_datasets: string[];
  shared_dimensions: string[];
  relations: CrossDatasetRelation[];
  cross_hypotheses: string[];
}

// -- Top-level AI Report ---------------------------------------------------

export interface AIInvestigationReport {
  investigation_report: InvestigationReport;
  narrative: Narrative | null;
  model_metadata: ModelMetadata | null;
  interactive_investigation: InteractiveInvestigationReport | null;
  investigation_graph: InvestigationGraph | null;
}
