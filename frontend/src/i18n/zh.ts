import type { Translations } from "./translations";

const zh: Translations = {
  common: {
    appName: "Investigative Analyst",
    languageLabel: "语言",
    themeLabel: "主题",
  },

  home: {
    heading: "Investigative Data Analyst",
    subtitle:
      "上传 CSV 文件，获取 AI 驱动的调查报告——包含信号检测、证据验证、假设检验和可执行的后续步骤。这不是仪表盘，这是一位分析师。",
    cta: "开始调查",
    features: {
      signals: {
        title: "信号检测",
        desc: "8 种信号类型——异常值、趋势、偏度、集中度等。",
      },
      evidence: {
        title: "证据驱动",
        desc: "每个假设在呈现之前都经过统计证据验证。",
      },
      narrative: {
        title: "AI 叙事",
        desc: "用自然语言解释分析结果，而不是简单罗列数据。",
      },
    },
  },

  investigation: {
    tabs: {
      overview: "概览",
      findings: "发现",
      narrative: "叙事",
      interactive: "下一步",
    },
    loading: {
      processing: "正在分析您的数据集...",
      starting: "正在启动调查...",
      stages: {
        parsing: "解析文件",
        profiling: "数据画像",
        signals: "信号检测",
        evidence: "证据收集",
        validation: "假设验证",
        report: "报告生成",
        narrative: "AI 叙事生成",
      },
    },
    error: {
      title: "调查失败",
      default: "发生了意外错误。",
    },
    overview: {
      executiveSummary: "执行摘要",
      dataset: "数据集",
      hypotheses: "假设",
      supported: "已支持",
      refuted: "已驳回",
      riskLevel: "风险等级",
      highestPriority: "最高优先级发现",
      rowsColumns: (rows, cols) => `${rows} 行 × ${cols} 列`,
    },
    findings: {
      empty: "没有可显示的发现。",
    },
    narrative: {
      empty: "本次调查未生成叙事报告。",
      executiveSummary: "执行摘要",
      keyFindings: "关键发现",
      businessImpact: "业务影响",
      recommendations: "建议",
      generatedBy: (provider, model, version) =>
        `由 ${provider}/${model} 生成 · 提示词 v${version}`,
    },
    interactive: {
      empty: "没有可用的交互式调查数据。",
      followUp: "后续问题",
      dataGaps: "数据缺口",
      paths: "调查路径",
      source: "来源",
    },
    status: {
      supported: "已支持",
      refuted: "已驳回",
      inconclusive: "未确定",
    },
  },
};

export default zh;
