from app.schemas.evidence import Evidence


METRIC_DISPLAY_METADATA: dict[str, tuple[str, str]] = {
    "growth_rate": ("变化率", "percent"),
    "absolute_change": ("绝对变化", "number"),
    "trend_slope": ("趋势斜率", "number"),
    "trend_points": ("趋势点数", "integer"),
    "r_squared": ("拟合质量 R²", "number"),
    "first_val": ("起始值", "number"),
    "last_val": ("结束值", "number"),
    "mean": ("平均值", "number"),
    "median": ("中位数", "number"),
    "std": ("标准差", "number"),
    "skewness": ("偏度系数", "number"),
    "count": ("样本数", "integer"),
    "top_1_share": ("第一大类别占比", "percent"),
    "top_2_share": ("前二类别占比", "percent"),
    "top_3_share": ("前三类别占比", "percent"),
    "outlier_count": ("异常值数量", "integer"),
    "outlier_ratio": ("异常值占比", "percent"),
    "iqr_lower_bound": ("IQR 下界", "number"),
    "iqr_upper_bound": ("IQR 上界", "number"),
    "null_percentage": ("缺失率", "percent_point"),
    "unique_count": ("唯一值数量", "integer"),
    "unique_ratio": ("唯一值占比", "percent"),
    "coefficient_of_variation": ("变异系数", "percent"),
}


def add_display_metadata(evidence: Evidence) -> Evidence:
    """Attach presentation metadata without moving display logic into schemas."""
    if evidence.metric is None:
        return evidence

    metadata = METRIC_DISPLAY_METADATA.get(evidence.metric)
    if metadata is None:
        return evidence

    label, display_format = metadata
    update: dict[str, str] = {}
    if evidence.display_label is None:
        update["display_label"] = label
    if evidence.display_format is None:
        update["display_format"] = display_format

    return evidence.model_copy(update=update) if update else evidence
