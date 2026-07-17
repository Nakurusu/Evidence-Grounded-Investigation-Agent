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
# Finding templates (Simplified Chinese)
# ---------------------------------------------------------------------------

_FINDING_TEMPLATES: dict[SignalType, dict[HypothesisStatus, dict[str, str]]] = {
    # -- RIGHT_SKEWED -------------------------------------------------------
    SignalType.RIGHT_SKEWED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 呈右偏分布：均值 ({mean}) 显著高于中位数 "
                "({median})，偏度系数={skewness}。"
            ),
            "analysis": (
                "偏度系数 ({skewness}) 为正，确认少数高值记录将平均值拉高至"
                "典型值之上。均值不能代表大多数观测值。"
            ),
            "business_impact": (
                "基于均值的业务指标可能误导决策。仅依赖均值进行绩效评估会高估"
                "典型表现。业务可能依赖少数高价值交易、客户或产品。"
            ),
            "recommendation": (
                "对 '{column}' 进行分段分析，将高值异常值与典型群体区分开。"
                "使用中位数指标进行基线报告。调查高值记录是可持续业务还是"
                "一次性事件。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在右偏分布，但偏度系数 "
                "({skewness}) 未确认有意义右偏。"
            ),
            "analysis": (
                "统计证据不支持右偏假设。分布可能近似对称，或样本量不足以"
                "检测偏度。"
            ),
            "business_impact": (
                "该维度未发现头部集中的风险。标准统计指标（均值、标准差）"
                "适用于报告。"
            ),
            "recommendation": (
                "暂不需要采取行动。如数据量增加或业务场景提示存在隐藏的"
                "集中风险，请重新评估。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在右偏分布，但证据不足以确认"
                "或否定该模式。"
            ),
            "analysis": (
                "现有指标无法确定性地验证偏度假设。可能原因：数据不足、"
                "指标值缺失或分布处于边界状态。"
            ),
            "business_impact": (
                "无法确定该维度的业务均值是否可靠。基于 '{column}' 均值的"
                "决策应谨慎。"
            ),
            "recommendation": (
                "收集更多数据或检查 '{column}' 的数据质量。在做出业务结论"
                "前，建议手动检查分布情况。"
            ),
        },
    },
    # -- LEFT_SKEWED --------------------------------------------------------
    SignalType.LEFT_SKEWED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 呈左偏分布：均值 ({mean}) 低于中位数 "
                "({median})，偏度系数={skewness}。"
            ),
            "analysis": (
                "偏度系数 ({skewness}) 为负，表明少数异常低值将平均值拉低。"
                "均值低估了典型值水平。"
            ),
            "business_impact": (
                "业务均值可能低估了典型表现。少数低绩效记录可能正在扭曲"
                "整体指标。如果这些记录反映实际业务事件，值得深入调查。"
            ),
            "recommendation": (
                "调查 '{column}' 中的低值记录，确定其是否反映数据错误、"
                "特殊情况或系统性低绩效。排除或分段处理以获得更清晰的报告。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在左偏分布，但偏度系数 "
                "({skewness}) 未确认有意义左偏。"
            ),
            "analysis": (
                "统计证据不支持左偏假设。分布可能近似对称。"
            ),
            "business_impact": (
                "该维度未发现系统性低绩效偏差。标准报告指标应该是可靠的。"
            ),
            "recommendation": (
                "暂不需要采取行动。如新数据出现低端异常值迹象，请重新评估。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在左偏分布，但证据不足以确认"
                "或否定该模式。"
            ),
            "analysis": (
                "现有指标无法确定性地验证左偏假设。分布可能处于边界状态。"
            ),
            "business_impact": (
                "无法确定低值记录是否实质性扭曲了 '{column}' 的均值。"
            ),
            "recommendation": (
                "收集更多数据或手动检查 '{column}' 的分布情况。"
            ),
        },
    },
    # -- OUTLIER_DETECTED ---------------------------------------------------
    SignalType.OUTLIER_DETECTED: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 包含 {outlier_count} 个异常值，占数据总量的 "
                "{outlier_ratio:.1%}。IQR 边界：[{iqr_lower_bound}, "
                "{iqr_upper_bound}]。"
            ),
            "analysis": (
                "在 '{column}' 中发现 {outlier_count} 个异常值（占比 "
                "{outlier_ratio:.1%}），确认存在异常数据。这些异常值可能"
                "反映真实业务事件、数据录入错误或罕见但合法的交易。"
            ),
            "business_impact": (
                "异常值可能显著扭曲聚合指标（总计、均值），如处理不当会"
                "导致错误业务决策。如果异常值代表真实事件，则可能预示"
                "新兴风险或机会。"
            ),
            "recommendation": (
                "逐一审查 '{column}' 中的 {outlier_count} 个异常记录。"
                "分类为：数据错误（修正）、合法罕见事件（记录）或未知"
                "（持续监控）。考虑在基线报告中排除异常值。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在异常值，但证据显示仅有 "
                "{outlier_count} 个异常值，未确认有意义的异常模式。"
            ),
            "analysis": (
                "异常值检测信号未获证据验证。被标记的值可能落在预期范围"
                "内，或反映正常波动。"
            ),
            "business_impact": (
                "'{column}' 未发现确认的异常值风险。标准报告可正常进行。"
            ),
            "recommendation": (
                "暂不需要采取行动。在后续数据加载中继续监控 '{column}' "
                "是否出现新的异常值。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在异常值，但证据不足以确认"
                "或否定。"
            ),
            "analysis": (
                "数据或指标不足以验证 '{column}' 的异常值信号。"
            ),
            "business_impact": (
                "无法确定异常值是否实质性影响 '{column}' 的指标。"
            ),
            "recommendation": (
                "收集更多数据或手动检查 '{column}' 中的异常值。"
            ),
        },
    },
    # -- INCREASING_TREND ---------------------------------------------------
    SignalType.INCREASING_TREND: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 呈上升趋势：从 {first_val} 变化至 "
                "{last_val}（增长率：{growth_rate:.1%}）。"
            ),
            "analysis": (
                "{growth_rate:.1%} 的正增长率确认 '{column}' 处于上升轨道。"
                "该趋势可能由有机增长、市场扩张或定价变化驱动。"
            ),
            "business_impact": (
                "'{column}' 的持续增长是积极信号，但需要了解驱动因素。"
                "如果增长集中在少数细分市场，可能不可持续；如果是广泛"
                "增长，则表明健康的业务势头。"
            ),
            "recommendation": (
                "按细分维度（地区、产品、客户群）拆解 '{column}' 的增长，"
                "识别驱动因素。评估增长率是在加速、稳定还是减速。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在上升趋势，但增长率 "
                "({growth_rate:.1%}) 未确认有意义的上升轨迹。"
            ),
            "analysis": (
                "'{column}' 中观察到的变化太小或不一致，无法确认真正的"
                "上升趋势。"
            ),
            "business_impact": (
                "'{column}' 未确认增长趋势。在没有进一步证据的情况下，"
                "业务规划不应假设该维度存在上升势头。"
            ),
            "recommendation": (
                "在更长时间范围内监控 '{column}'，以检测趋势是否形成。"
                "单期变化不足以作为趋势判断的依据。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在上升趋势，但证据不足以验证。"
            ),
            "analysis": (
                "数据点或指标不足以确认或否定 '{column}' 的上升趋势。"
            ),
            "business_impact": (
                "无法确定 '{column}' 是否真正呈上升趋势。"
            ),
            "recommendation": (
                "收集更多 '{column}' 的时间序列数据以支持趋势验证。"
            ),
        },
    },
    # -- DECREASING_TREND ---------------------------------------------------
    SignalType.DECREASING_TREND: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 呈下降趋势：从 {first_val} 变化至 "
                "{last_val}（变化率：{growth_rate:.1%}）。"
            ),
            "analysis": (
                "{growth_rate:.1%} 的负增长率确认 '{column}' 处于下降轨道。"
                "这可能表示客户流失、需求下降、竞争压力或主动业务调整。"
            ),
            "business_impact": (
                "'{column}' 的持续下降构成业务风险。如果趋势在未加干预的"
                "情况下持续，可能导致显著的收入或业务量损失。尽早诊断"
                "原因至关重要。"
            ),
            "recommendation": (
                "调查 '{column}' 下降的驱动因素：按细分维度拆解，确定"
                "下降是广泛性的还是集中性的。如有行业基准数据，进行对比。"
                "制定客户保留或业务扭转计划。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在下降趋势，但变化率 "
                "({growth_rate:.1%}) 未确认有意义的下降。"
            ),
            "analysis": (
                "'{column}' 中观察到的变化太小或不一致，无法确认真正的"
                "下降趋势。"
            ),
            "business_impact": (
                "'{column}' 未确认下降趋势。在没有进一步证据的情况下，"
                "业务规划不应假设存在负面势头。"
            ),
            "recommendation": (
                "在更长时间范围内监控 '{column}'。短期下降不一定是"
                "结构性趋势。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在下降趋势，但证据不足以验证。"
            ),
            "analysis": (
                "数据点或指标不足以确认或否定 '{column}' 的下降趋势。"
            ),
            "business_impact": (
                "无法确定 '{column}' 是否真正在下降。"
            ),
            "recommendation": (
                "收集更多 '{column}' 的时间序列数据以支持趋势验证。"
            ),
        },
    },
    # -- HIGH_CONCENTRATION -------------------------------------------------
    SignalType.HIGH_CONCENTRATION: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 呈高度集中：最大单一贡献者占总量的 "
                "{top_1_share:.1%}，前 3 名合计占 {top_3_share:.1%}。"
            ),
            "analysis": (
                "{top_1_share:.1%} 的价值集中在单一类别中，业务存在显著"
                "依赖风险。前 3 名合计占比 {top_3_share:.1%} 确认这是"
                "结构性模式，而非单一异常值。"
            ),
            "business_impact": (
                "高度集中意味着业务表现严重依赖少数实体（客户、产品或"
                "地区）。任何影响头部贡献者的变化都会对整体结果产生不成"
                "比例的影响。这是关键业务风险。"
            ),
            "recommendation": (
                "评估 '{column}' 中头部贡献者的稳定性和流失风险。如果"
                "集中度超出风险承受范围，制定多元化策略。为头部实体设置"
                "预警监控。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在集中风险，但头部贡献者占比"
                "({top_1_share:.1%}) 未确认有意义的集中风险。"
            ),
            "analysis": (
                "'{column}' 的集中度在可接受范围内。没有单一类别主导分布。"
            ),
            "business_impact": (
                "业务表现在 '{column}' 各维度上分布合理。暂无集中风险。"
            ),
            "recommendation": (
                "随着业务组合变化，定期检查 '{column}' 的集中度。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在集中风险，但证据不足以验证。"
            ),
            "analysis": (
                "无法从现有证据确定 '{column}' 的真实集中度。"
            ),
            "business_impact": (
                "无法评估 '{column}' 的集中风险。多元化决策可能为时过早。"
            ),
            "recommendation": (
                "收集 '{column}' 的更细粒度数据，或在评估集中度前核实"
                "分类定义。"
            ),
        },
    },
    # -- HIGH_MISSING_RATE --------------------------------------------------
    SignalType.HIGH_MISSING_RATE: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 的缺失率为 {null_percentage:.1f}%。"
            ),
            "analysis": (
                "{null_percentage:.1f}% 的缺失率显著偏高，可能影响涉及 "
                "'{column}' 的任何分析的可靠性。缺失数据可能是随机的或"
                "系统性的——后者更危险，因为会引入偏差。"
            ),
            "business_impact": (
                "基于 '{column}' 得出的结论可能不可靠或存在偏差。如果该"
                "列用于业务决策（如收入报告、客户评分），缺失数据可能"
                "导致错误行动。"
            ),
            "recommendation": (
                "调查 '{column}' 缺失数据的根本原因：是数据收集缺失、"
                "系统问题还是合法的「不适用」情况？如果该数据至关重要，"
                "考虑填补策略或流程改进以降低缺失率。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在高缺失率，但实际缺失率"
                "({null_percentage:.1%}%) 在可接受范围内。"
            ),
            "analysis": (
                "'{column}' 的缺失率足够低，不太可能实质性影响分析结果。"
            ),
            "business_impact": (
                "'{column}' 的数据质量足以满足业务报告和分析需求。"
            ),
            "recommendation": (
                "作为常规数据质量检查的一部分，持续监控 '{column}' 的"
                "缺失率。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在高缺失率，但证据不足以验证。"
            ),
            "analysis": (
                "无法确定 '{column}' 的真实缺失率及其影响。"
            ),
            "business_impact": (
                "'{column}' 的数据质量不确定。依赖此列做决策时请谨慎。"
            ),
            "recommendation": (
                "核实 '{column}' 的缺失值计算，评估缺失是随机的还是"
                "系统性的。"
            ),
        },
    },
    # -- HIGH_CARDINALITY ---------------------------------------------------
    SignalType.HIGH_CARDINALITY: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 包含 {unique_count} 个唯一值（占行数的 "
                "{unique_ratio:.1%}）。"
            ),
            "analysis": (
                "唯一值比例达 {unique_ratio:.1%}，'{column}' 更像是一个"
                "标识符而非分类维度。其不同值过多，无法有效用于分组或"
                "聚合分析。"
            ),
            "business_impact": (
                "'{column}' 在当前形式下无法有效用作分析维度。尝试按此列"
                "分组或聚合将产生无意义的结果（每组仅一行）。"
            ),
            "recommendation": (
                "判断 '{column}' 是否为标识符（应排除在分析之外），或是否"
                "应聚合到更广泛的类别中。如果属于分类变量，考虑分箱、聚类"
                "或提取更高层级的分组。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在高基数，但唯一值比例"
                "({unique_ratio:.1%}) 在可接受范围内。"
            ),
            "analysis": (
                "'{column}' 的不同值数量合理，可以作为分组维度使用。"
            ),
            "business_impact": (
                "'{column}' 适合用作报告和聚合中的分析维度。"
            ),
            "recommendation": (
                "无需处理。'{column}' 可正常用于分组和细分分析。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在高基数，但证据不足以验证。"
            ),
            "analysis": (
                "无法确定 '{column}' 的唯一值数量是否会对分析使用造成问题。"
            ),
            "business_impact": (
                "按 '{column}' 分组时请谨慎——结果可能过于细碎。"
            ),
            "recommendation": (
                "检查 '{column}' 的不同值，判断是否需要进行分箱或归类。"
            ),
        },
    },
    # -- LOW_VARIANCE -------------------------------------------------------
    SignalType.LOW_VARIANCE: {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "列 '{column}' 的方差非常低：变异系数 = "
                "{coefficient_of_variation:.2%}，标准差 = {std}。"
            ),
            "analysis": (
                "变异系数为 {coefficient_of_variation:.2%}，表明 "
                "'{column}' 的值几乎不偏离均值。该列几乎没有区分能力。"
            ),
            "business_impact": (
                "'{column}' 提供的分析价值很低——无法区分好坏表现者、"
                "识别趋势或细分人群。将其纳入分析只会增加噪音而没有"
                "洞察价值。"
            ),
            "recommendation": (
                "考虑降低 '{column}' 的分析优先级或将其排除。如果该列"
                "本应存在变化（如客户评分、价格），调查其为何保持不变"
                "——这本身可能就是一个发现。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "列 '{column}' 被标记为可能存在低方差，但变异系数 "
                "({coefficient_of_variation:.2%}) 未确认存在问题。"
            ),
            "analysis": (
                "'{column}' 显示出足够的变异性，具有分析价值。"
            ),
            "business_impact": (
                "'{column}' 具有足够的区分能力，可用于细分和分析。"
            ),
            "recommendation": (
                "无需处理。'{column}' 可正常用于分析。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "列 '{column}' 被标记为可能存在低方差，但证据不足以验证。"
            ),
            "analysis": (
                "无法确定 '{column}' 的方差是否足以支持分析。"
            ),
            "business_impact": (
                "'{column}' 的分析价值不确定。"
            ),
            "recommendation": (
                "收集更多数据或手动检查 '{column}' 的值以评估其方差。"
            ),
        },
    },
}

# ---------------------------------------------------------------------------
# Composite templates (Simplified Chinese)
# ---------------------------------------------------------------------------

_COMPOSITE_TEMPLATES: dict[frozenset[SignalType], dict[HypothesisStatus, dict[str, str]]] = {
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "数据集同时呈现高度集中和右偏分布，表明少数实体主导了"
                "业务结果。"
            ),
            "analysis": (
                "集中度与右偏共现是头部集中型业务结构的强信号。少数"
                "高值记录不成比例地驱动着聚合指标。"
            ),
            "business_impact": (
                "业务在结构上依赖少数实体。这造成了脆弱性——头部贡献者"
                "的任何变化都会对整体表现产生巨大影响。增长可能也是集中"
                "而非广泛分布的。"
            ),
            "recommendation": (
                "这是高优先级发现。梳理头部贡献者并评估其稳定性。制定"
                "多元化策略，并将集中度监控设为关键风险指标。分段报告应"
                "将头部贡献者与长尾区分开来。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "集中度与右偏的组合模式未获现有证据确认。"
            ),
            "analysis": (
                "证据不支持集中度与偏度组合风险的假设。业务结构可能比"
                "最初判断更均衡。"
            ),
            "business_impact": (
                "未确认集中度-偏度组合带来的结构性依赖风险。"
            ),
            "recommendation": (
                "如有新数据可用时重新评估。目前标准监控即可。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "可能存在集中度与偏度组合模式，但证据不足以确认或否定。"
            ),
            "analysis": (
                "部分信号提示存在头部集中结构，但证据不完整或矛盾。"
            ),
            "business_impact": (
                "存在潜在的结构性依赖风险——无法确认或排除。"
            ),
            "recommendation": (
                "收集更细粒度的数据并重新分析。在此期间手动审查头部"
                "贡献者的集中度。"
            ),
        },
    },
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.INCREASING_TREND}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "业务增长与高度集中同时存在。增长可能主要由少数实体驱动。"
            ),
            "analysis": (
                "上升趋势与高集中度的组合表明增长并非广泛分布。少数头部"
                "贡献者可能贡献了大部分上升势头。"
            ),
            "business_impact": (
                "依赖少数实体的增长是脆弱的。如果头部贡献者停滞或流失，"
                "整体增长可能迅速逆转。报告的增长数据可能高估了业务的"
                "整体健康程度。"
            ),
            "recommendation": (
                "将增长拆解为头部实体与其余实体的贡献。评估增长集中度"
                "是否随时间上升。考虑扩大增长基础的战略。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "集中度与增长的组合模式未获现有证据确认。"
            ),
            "analysis": (
                "证据不支持增长集中在少数实体的假设。"
            ),
            "business_impact": (
                "增长分布似乎合理。未确认集中度驱动的增长风险。"
            ),
            "recommendation": (
                "持续监控。如集中度指标发生变化，请重新评估。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "可能存在增长集中模式，但证据不足以验证。"
            ),
            "analysis": (
                "部分信号提示增长可能集中，但证据不完整。"
            ),
            "business_impact": (
                "增长质量不确定——无法判断增长是广泛的还是集中"
                "在少数实体。"
            ),
            "recommendation": (
                "收集细分维度的趋势数据以评估增长分布。"
            ),
        },
    },
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.DECREASING_TREND}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "业务下滑发生在高度集中的结构中。下滑可能由头部贡献者"
                "驱动。"
            ),
            "analysis": (
                "当高集中度与下降趋势共存时，表明主导实体正在经历衰退，"
                "从而拉低整体结果。这是比广泛性下降风险更高的模式。"
            ),
            "business_impact": (
                "业务面临双重风险：依赖少数实体，而这些实体正在衰退。"
                "如果趋势持续，集中度将放大影响。这需要紧急关注。"
            ),
            "recommendation": (
                "优先对头部衰退实体的保留和扭转工作。同时加速多元化以"
                "减少依赖。为头部贡献者设置实时监控。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "集中度与下降的组合模式未获现有证据确认。"
            ),
            "analysis": (
                "证据不支持下降集中在头部实体的假设。"
            ),
            "business_impact": (
                "观察到的下降可能是广泛性的，而非由头部实体疲弱驱动。"
            ),
            "recommendation": (
                "调查所有细分维度的下降驱动因素，而非仅关注头部实体。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "可能存在集中度驱动的下降，但证据不足以验证。"
            ),
            "analysis": (
                "信号提示存在头部实体衰退风险，但证据不完整。"
            ),
            "business_impact": (
                "集中性衰退风险无法确认或排除。"
            ),
            "recommendation": (
                "收集实体级别的趋势数据以评估下降是否集中。"
            ),
        },
    },
    frozenset({SignalType.OUTLIER_DETECTED, SignalType.RIGHT_SKEWED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "异常值和右偏分布同时存在，表明极端高值正在扭曲整体"
                "统计数据。"
            ),
            "analysis": (
                "异常值与右偏的组合表明极端值不仅存在，而且正在实质性"
                "影响数据分布。这些异常值很可能是观察到的偏度的原因。"
            ),
            "business_impact": (
                "报告的均值和总额可能被少数极端记录显著夸大。基于这些"
                "聚合指标的业务决策可能过于乐观。「典型」表现很可能低于"
                "报告均值所显示的水平。"
            ),
            "recommendation": (
                "逐一审查异常记录。确定它们是合法的（保留并记录）、"
                "错误的（更正或删除）还是一次性事件（从基线中排除）。"
                "重新计算包含和不包含异常值的关键指标，量化扭曲程度。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "异常值与偏度的组合模式未获现有证据确认。"
            ),
            "analysis": (
                "证据不支持极端值造成实质性扭曲。"
            ),
            "business_impact": (
                "报告的统计数据可能代表了真实的业务状况。"
            ),
            "recommendation": (
                "暂不需要采取行动。标准异常值监控即可。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "可能存在异常值驱动的偏度，但证据不足以验证。"
            ),
            "analysis": (
                "异常值和偏度信号存在，但证据不完整或矛盾。"
            ),
            "business_impact": (
                "无法确定极端值是否实质性扭曲了业务指标。"
            ),
            "recommendation": (
                "手动审查被标记的异常记录，评估其业务重要性。"
            ),
        },
    },
    frozenset({SignalType.HIGH_MISSING_RATE, SignalType.OUTLIER_DETECTED}): {
        HypothesisStatus.SUPPORTED: {
            "observation": (
                "同一数据集中同时存在高缺失率和异常值，表明数据质量问题"
                "可能正在影响分析可靠性。"
            ),
            "analysis": (
                "缺失数据与异常值共现是数据质量的红旗信号。缺失值可能"
                "在制造人为异常值，或者相同的潜在流程问题可能同时导致"
                "了这两种现象。"
            ),
            "business_impact": (
                "由于复合数据质量问题，分析结果可能不可靠。基于此数据"
                "的决策存在较高的出错风险。根本原因可能是系统性的数据"
                "收集或处理问题。"
            ),
            "recommendation": (
                "优先进行数据质量审查。调查缺失数据和异常值是否共享"
                "共同原因（如系统错误、流程缺陷）。在从受影响列得出"
                "业务结论之前，先解决数据质量问题。"
            ),
        },
        HypothesisStatus.REFUTED: {
            "observation": (
                "复合数据质量风险模式未获现有证据确认。"
            ),
            "analysis": (
                "证据不支持存在复合数据质量问题的假设。"
            ),
            "business_impact": (
                "数据质量似乎足以支撑可靠的分析。"
            ),
            "recommendation": (
                "继续进行常规数据质量监控。"
            ),
        },
        HypothesisStatus.INCONCLUSIVE: {
            "observation": (
                "可能存在复合数据质量问题，但证据不足以验证。"
            ),
            "analysis": (
                "缺失数据和异常值信号存在，但无法确定性地关联。"
            ),
            "business_impact": (
                "数据可靠性不确定——在基于受影响列做出业务决策时请谨慎。"
            ),
            "recommendation": (
                "对受影响列进行人工数据质量评估。"
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _build_context(vh: ValidatedHypothesis) -> dict:
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
    try:
        return template.format(**ctx)
    except (KeyError, ValueError):
        return template


# ---------------------------------------------------------------------------
# Finding builders
# ---------------------------------------------------------------------------

def _build_simple_finding(vh: ValidatedHypothesis) -> Finding:
    signal_type = vh.hypothesis.supporting_signals[0]
    status = vh.status
    ctx = _build_context(vh)

    templates = _FINDING_TEMPLATES.get(signal_type, {}).get(status)
    if templates is None:
        return Finding(
            title=vh.hypothesis.title,
            observation=f"{vh.hypothesis.description}",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="该发现暂无详细分析模板。",
            business_impact="无法自动评估业务影响。",
            recommendation="建议人工审查。",
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
    signal_key = frozenset(vh.hypothesis.supporting_signals)
    status = vh.status
    ctx = _build_context(vh)

    composite = _COMPOSITE_TEMPLATES.get(signal_key, {}).get(status)
    if composite is None:
        return Finding(
            title=vh.hypothesis.title,
            observation=f"检测到组合信号模式：{', '.join(s.value for s in vh.hypothesis.supporting_signals)}。",
            status=status,
            confidence=vh.adjusted_confidence,
            supporting_evidence=vh.supporting_evidence,
            contradicting_evidence=vh.contradicting_evidence,
            analysis="该组合发现暂无详细分析模板。",
            business_impact="无法自动评估业务影响。",
            recommendation="建议对组合信号进行人工审查。",
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
    findings = [
        _build_finding(vh) for vh in validation_report.validated
    ]

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
