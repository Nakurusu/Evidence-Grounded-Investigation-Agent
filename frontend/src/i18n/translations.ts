/* ------------------------------------------------------------------ */
/*  Translation keys — the single source of truth for i18n.           */
/*  Every key here must be implemented in both zh.ts and en.ts.       */
/* ------------------------------------------------------------------ */

export interface Translations {
  common: {
    appName: string;
    languageLabel: string;
    themeLabel: string;
  };

  home: {
    heading: string;
    subtitle: string;
    cta: string;
    features: {
      signals: { title: string; desc: string };
      evidence: { title: string; desc: string };
      narrative: { title: string; desc: string };
    };
    questionInput: {
      label: string;
      placeholder: string;
      help: string;
    };
  };

  investigation: {
    tabs: {
      overview: string;
      findings: string;
      narrative: string;
      interactive: string;
    };
    loading: {
      processing: string;
      starting: string;
      stages: {
        parsing: string;
        profiling: string;
        signals: string;
        questions: string;
        hypotheses: string;
        evidence: string;
        validation: string;
        report: string;
        narrative: string;
        interactive: string;
        secondary_profiling: string;
        cross_dataset: string;
        completed: string;
      };
      elapsed: (elapsed: string) => string;
      completedCount: (completed: number, total: number) => string;
      fallbackDetail: string;
      currentStage: string;
      stageInput: string;
      stageOutput: string;
      stageReason: string;
    };
    error: {
      title: string;
      default: string;
    };
    overview: {
      executiveSummary: string;
      investigationQuestion: string;
      explorationMode: string;
      dataset: string;
      hypotheses: string;
      supported: string;
      refuted: string;
      inconclusive: string;
      riskLevel: string;
      confidence: string;
      highestPriority: string;
      causeCandidates: string;
      candidateScore: string;
      candidateEvidence: string;
      candidateLimitations: string;
      candidateNextStep: string;
      noCauseCandidates: string;
      rowsColumns: (rows: number, cols: number) => string;
      columnTypes: {
        numeric: string;
        categorical: string;
        datetime: string;
        text: string;
        boolean: string;
      };
      columnRoles: {
        title: string;
        metric: string;
        dimension: string;
        time: string;
        entity: string;
        identifier: string;
      };
      quality: string;
      qualityRisk: string;
      noQualityIssues: string;
    };
    findings: {
      empty: string;
      all: string;
      clear: string;
      noFilterMatch: string;
      count: (shown: number, total: number) => string;
      moreDetail: string;
      lessDetail: string;
      analysis: string;
      businessImpact: string;
      supportingEvidence: string;
      contradictingEvidence: string;
      recommendation: string;
      affectedColumns: string;
      keyMetrics: string;
      evidenceTrace: string;
      evidenceStrength: string;
      uncertaintyNotes: string;
      method: string;
      threshold: string;
      sampleSize: string;
      limitation: string;
    };
    narrative: {
      empty: string;
      executiveSummary: string;
      keyFindings: string;
      evidenceSummary: string;
      businessImpact: string;
      recommendations: string;
      plainLanguageSummary: string;
      whatHappened: string;
      whyItMatters: string;
      whatToCheckNext: string;
      confidenceNotes: string;
      generatedBy: (provider: string, model: string, version: string) => string;
    };
    interactive: {
      empty: string;
      followUp: string;
      dataGaps: string;
      paths: string;
      source: string;
      unresolvedAreas: string;
      affects: string;
      runDrilldown: string;
      running: string;
      runFailed: string;
      drilldownResults: string;
      drilldownStatus: {
        completed: string;
        unsupported: string;
      };
      drilldownAnalysisType: {
        tail_records: string;
        trend_by_dimension: string;
        top_category_vs_rest: string;
        missingness_by_dimension: string;
        cardinality_distribution: string;
        low_variance_distribution: string;
        unsupported: string;
      };
      questionCategory: {
        drill_down: string;
        data_gap: string;
        alternative_explanation: string;
        cross_pattern: string;
      };
    };
    crossDataset: {
      tab: string;
      title: string;
      primary: string;
      secondary: string;
      sharedDimensions: string;
      relations: (count: number) => string;
      hypotheses: string;
    };
    status: {
      supported: string;
      refuted: string;
      inconclusive: string;
    };
    confidence: {
      high: string;
      medium: string;
      low: string;
    };
  };
}
