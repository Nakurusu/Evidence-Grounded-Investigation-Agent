const METRIC_LABELS: Record<string, string> = {
  growth_rate: "变化率",
  absolute_change: "绝对变化",
  trend_slope: "趋势斜率",
  trend_points: "趋势点数",
  r_squared: "拟合质量 R²",
  first_val: "起始值",
  last_val: "结束值",
  mean: "平均值",
  median: "中位数",
  std: "标准差",
  skewness: "偏度系数",
  count: "样本数",
  top_1_share: "第一大类别占比",
  top_2_share: "前二类别占比",
  top_3_share: "前三类别占比",
  outlier_count: "异常值数量",
  outlier_ratio: "异常值占比",
  iqr_lower_bound: "IQR 下界",
  iqr_upper_bound: "IQR 上界",
  null_percentage: "缺失率",
  unique_count: "唯一值数量",
  unique_ratio: "唯一值占比",
  coefficient_of_variation: "变异系数",
};

const PERCENT_METRICS = new Set([
  "growth_rate",
  "top_1_share",
  "top_2_share",
  "top_3_share",
  "outlier_ratio",
  "unique_ratio",
  "coefficient_of_variation",
]);

const PERCENT_POINT_METRICS = new Set([
  "null_percentage",
]);

export function metricLabel(metric: string | null): string {
  if (!metric) return "指标";
  return METRIC_LABELS[metric] ?? metric;
}

export function formatMetricValue(
  metric: string | null,
  value: string | number | null,
): string {
  if (value === null || value === undefined) return "N/A";
  if (typeof value === "string") return value;
  if (PERCENT_METRICS.has(metric ?? "")) {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (PERCENT_POINT_METRICS.has(metric ?? "")) {
    return `${value.toFixed(1)}%`;
  }
  if (Number.isInteger(value)) return String(value);
  return value.toLocaleString(undefined, {
    maximumFractionDigits: 3,
  });
}
