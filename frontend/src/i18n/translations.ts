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
        evidence: string;
        validation: string;
        report: string;
        narrative: string;
      };
    };
    error: {
      title: string;
      default: string;
    };
    overview: {
      executiveSummary: string;
      dataset: string;
      hypotheses: string;
      supported: string;
      refuted: string;
      riskLevel: string;
      highestPriority: string;
      rowsColumns: (rows: number, cols: number) => string;
    };
    findings: {
      empty: string;
    };
    narrative: {
      empty: string;
      executiveSummary: string;
      keyFindings: string;
      businessImpact: string;
      recommendations: string;
      generatedBy: (provider: string, model: string, version: string) => string;
    };
    interactive: {
      empty: string;
      followUp: string;
      dataGaps: string;
      paths: string;
      source: string;
    };
    status: {
      supported: string;
      refuted: string;
      inconclusive: string;
    };
  };
}
