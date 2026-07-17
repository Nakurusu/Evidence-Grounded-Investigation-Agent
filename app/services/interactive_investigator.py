"""Interactive investigation engine — Phase 8 (Simplified Chinese).

Consumes the deterministic InvestigationReport and produces a forward-looking
InteractiveInvestigationReport: follow-up questions, data gaps, guided
investigation paths, and unresolved areas.
"""

from app.models.enums import SignalType, HypothesisStatus
from app.schemas.investigation_report import InvestigationReport, Finding
from app.schemas.interactive import (
    FollowUpQuestion,
    DataGap,
    InvestigationPath,
    InteractiveInvestigationReport,
)


# ---------------------------------------------------------------------------
# Follow-up question templates (zh-CN)
# ---------------------------------------------------------------------------

_DRILL_DOWN_TEMPLATES: dict[SignalType, list[dict]] = {
    SignalType.RIGHT_SKEWED: [
        {
            "question": "哪些具体记录或细分群体将 '{column}' 的均值拉高至中位数之上？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "'{column}' 的右偏在不同时间段是否一致，还是随时间变化？",
            "category": "drill_down",
            "required_data": ["{column} 的时间序列细分数据"],
        },
        {
            "question": "'{column}' 前 5% 的记录贡献了总价值的百分之多少？",
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.LEFT_SKEWED: [
        {
            "question": "哪些具体记录或细分群体将 '{column}' 的均值拉低至中位数之下？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "'{column}' 中的低值记录是数据错误、特殊情况还是系统性低绩效？",
            "category": "drill_down",
            "required_data": ["{column} 的业务元数据"],
        },
    ],
    SignalType.OUTLIER_DETECTED: [
        {
            "question": "'{column}' 中的异常值是否与特定类别、地区或时间段相关？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "'{column}' 中的异常值是数据录入错误还是真实的业务事件？",
            "category": "drill_down",
            "required_data": ["{column} 的交易级明细或审计日志"],
        },
        {
            "question": "排除 '{column}' 中的异常值后，关键指标和结论是否有实质性变化？",
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.HIGH_CONCENTRATION: [
        {
            "question": "'{column}' 中排名靠前的贡献者是谁？他们的流失风险有多高？",
            "category": "drill_down",
            "required_data": ["{column} 的实体级档案", "历史留存/流失数据"],
        },
        {
            "question": "'{column}' 的集中度是在持续上升还是下降？",
            "category": "drill_down",
            "required_data": ["集中度指标的时间序列数据"],
        },
        {
            "question": "'{column}' 的集中是结构性的（所有细分群体一致）还是由某一特定细分群体驱动的？",
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.INCREASING_TREND: [
        {
            "question": "'{column}' 的增长是广泛分布在多个细分群体，还是集中在少数群体中？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "是什么在驱动 '{column}' 的增长——新客户获取、价格上涨还是单客消费增加？",
            "category": "drill_down",
            "required_data": ["客户级交易数据", "定价历史"],
        },
        {
            "question": "'{column}' 的增长率是在加速、稳定还是减速？",
            "category": "drill_down",
            "required_data": ["{column} 的更长时间序列数据"],
        },
    ],
    SignalType.DECREASING_TREND: [
        {
            "question": "'{column}' 的下降是广泛性的还是集中在特定细分群体、产品或地区？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "'{column}' 的下降是近期才出现的还是长期趋势的一部分？",
            "category": "drill_down",
            "required_data": ["{column} 的更长时间序列数据"],
        },
        {
            "question": "是否有外部事件（市场变化、竞争行为、政策调整）与 '{column}' 的下降时间吻合？",
            "category": "data_gap",
            "required_data": ["外部市场数据", "竞争情报"],
        },
    ],
    SignalType.HIGH_MISSING_RATE: [
        {
            "question": "'{column}' 的缺失数据是随机的还是系统性的（例如集中在特定时间段、地区或类别）？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "是什么流程或系统缺陷导致了 '{column}' 的数据缺失？",
            "category": "data_gap",
            "required_data": ["数据采集流程文档", "系统日志"],
        },
    ],
    SignalType.HIGH_CARDINALITY: [
        {
            "question": "能否将 '{column}' 聚合为更少、更有意义的分组用于分析？",
            "category": "drill_down",
            "required_data": [],
        },
        {
            "question": "'{column}' 是否包含应合并的重复值或近似重复值？",
            "category": "drill_down",
            "required_data": [],
        },
    ],
    SignalType.LOW_VARIANCE: [
        {
            "question": "'{column}' 的低方差是预期内的（如固定价格产品）还是数据质量问题（如默认值、截断值）？",
            "category": "drill_down",
            "required_data": ["{column} 的业务背景信息"],
        },
        {
            "question": "是否存在方差更高且能更好地替代 '{column}' 的相关指标？",
            "category": "drill_down",
            "required_data": ["其他相关指标"],
        },
    ],
}

# ---------------------------------------------------------------------------
# Data gap recommendations (zh-CN)
# ---------------------------------------------------------------------------

_DATA_GAP_TEMPLATES: dict[SignalType, list[dict]] = {
    SignalType.HIGH_CONCENTRATION: [
        {
            "gap": "客户或实体细分数据（规模、行业、年限、细分市场）",
            "impact": "无法判断集中度是健康的（大型稳定实体）还是危险的（少数可能不稳定的实体）。",
            "suggested_source": "CRM 系统、客户主数据",
        },
        {
            "gap": "历史集中度趋势数据（往期数据）",
            "impact": "无法评估集中度是在改善（分散化）还是恶化（更加集中）。",
            "suggested_source": "历史财务报告、数据仓库",
        },
    ],
    SignalType.RIGHT_SKEWED: [
        {
            "gap": "头部实体的细分维度数据",
            "impact": "无法区分少数但稳定的大型贡献者与不可持续的一次性高峰。",
            "suggested_source": "交易级数据、实体档案",
        },
    ],
    SignalType.OUTLIER_DETECTED: [
        {
            "gap": "被标记记录的业务元数据或审计日志",
            "impact": "无法判断异常值是数据错误（可修复）还是合法的罕见事件（需监控）。",
            "suggested_source": "数据录入系统、业务数据库",
        },
    ],
    SignalType.DECREASING_TREND: [
        {
            "gap": "同期的外部基准或市场数据",
            "impact": "无法判断下降是公司特有现象还是行业普遍趋势。",
            "suggested_source": "行业报告、市场情报",
        },
        {
            "gap": "客户流失或留存数据",
            "impact": "无法判断下降是由于客户流失、客单价降低还是新客户减少。",
            "suggested_source": "CRM 系统、客户分析平台",
        },
    ],
    SignalType.INCREASING_TREND: [
        {
            "gap": "市场份额或竞争对手基准数据",
            "impact": "无法判断增长是市场份额的提升还是仅仅伴随市场红利。",
            "suggested_source": "行业报告、市场情报",
        },
    ],
    SignalType.HIGH_MISSING_RATE: [
        {
            "gap": "数据采集流程文档或系统日志",
            "impact": "无法判断数据缺失是系统问题（可通过工程修复）还是流程问题（需要工作流改进）。",
            "suggested_source": "工程团队、数据管道文档",
        },
    ],
    SignalType.LOW_VARIANCE: [
        {
            "gap": "同一维度的其他相关指标",
            "impact": "低方差列的分析价值有限。没有关联的替代指标，该维度无法为调查提供有效贡献。",
            "suggested_source": "业务团队、领域专家",
        },
    ],
    SignalType.HIGH_CARDINALITY: [
        {
            "gap": "该列的层级分类或业务分类体系",
            "impact": "没有定义的层级结构，无法将该列聚合为可供分析的分组。",
            "suggested_source": "数据治理团队、业务术语表",
        },
    ],
    SignalType.LEFT_SKEWED: [
        {
            "gap": "低值记录的业务背景信息",
            "impact": "无法判断低值是反映绩效不佳、特殊定价还是测量误差。",
            "suggested_source": "运营团队、定价数据库",
        },
    ],
}

# ---------------------------------------------------------------------------
# Investigation path templates (zh-CN)
# ---------------------------------------------------------------------------

_PATH_TEMPLATES: dict[SignalType, dict] = {
    SignalType.HIGH_CONCENTRATION: {
        "title": "调查 {column} 的集中度风险",
        "description": "梳理驱动 '{column}' 集中的实体，评估其稳定性，并探索多元化方案。",
        "steps": [
            "识别 '{column}' 中占总份额前 5-10 名的贡献者。",
            "分析每个头部贡献者：他们位居前列多久了？份额是在增长还是收缩？",
            "计算 '{column}' 的赫芬达尔指数（HHI），客观量化集中度水平。",
            "按规模十分位对 '{column}' 进行分段，分析各段的集中度。",
            "估算如果头部贡献者完全流失，对收入/价值的影响。",
            "建立月度集中度监控看板，超过阈值时发出预警。",
        ],
    },
    SignalType.DECREASING_TREND: {
        "title": "诊断 {column} 的下降原因",
        "description": "拆解 '{column}' 的下降趋势，识别根本驱动因素——是客户流失、消费减少还是其他原因？",
        "steps": [
            "按主要分类维度（地区、产品、细分市场）拆分 '{column}' 趋势，定位下降发生在哪些群体。",
            "将变化拆解为：(a) 交易/客户数量变化，(b) 单笔交易价值变化。",
            "将下降速度与历史时期比较——是在加速还是趋于稳定？",
            "如有客户级数据，将客户分为：增长、持平、下降、流失。量化各类占比。",
            "与相关业务领域的人员沟通，用定性背景验证定量发现。",
            "建立恢复情景模型：需要什么条件才能使 '{column}' 回到之前的水平？",
        ],
    },
    SignalType.INCREASING_TREND: {
        "title": "理解 {column} 的增长驱动因素",
        "description": "拆解 '{column}' 的增长，理解其是否可持续、是否广泛、是否高质量。",
        "steps": [
            "将增长拆解为：新客户获取、现有客户消费增加和价格变动。",
            "识别哪些细分群体（地区、产品、类别）在驱动增长——是广泛还是集中？",
            "计算客户群留存率：新客户是否留存，还是增长由一次性购买者驱动？",
            "如有行业基准数据，将增长率与市场平均水平进行对比。",
            "评估增长是否盈利：增长的边际成本是否可持续？",
            "设置先行指标，在增长放缓反映到聚合指标之前及时发现。",
        ],
    },
    SignalType.OUTLIER_DETECTED: {
        "title": "调查 {column} 中的异常记录",
        "description": "审查 '{column}' 中的异常记录，分类并确定应排除、监控还是进一步调查。",
        "steps": [
            "提取 '{column}' 中所有超出 IQR 边界的记录。",
            "对每个异常值，检查：属于哪个实体、哪个时间段、有哪些其他特征？寻找规律。",
            "将每个异常值分类：(A) 数据错误——修复源头，(B) 合法罕见事件——记录并监控，(C) 未知——标记为待人工审查。",
            "分别计算包含和不包含异常值的关键聚合指标（均值、总计、趋势），量化扭曲程度。",
            "如果异常值代表真实业务事件，为其建立单独的监控流程。",
        ],
    },
    SignalType.RIGHT_SKEWED: {
        "title": "分析 {column} 的右偏分布",
        "description": "理解 '{column}' 右偏的原因，以及是否代表集中风险。",
        "steps": [
            "绘制 '{column}' 的分布图，识别值变为极端值的拐点。",
            "分析 90 分位数以上的记录：属于哪些实体、发生在何时、属于哪些细分群体？",
            "计算前 1%、5%、10% 的记录贡献了 '{column}' 总值的百分比。",
            "比较均值与中位数随时间的变化——差距是在扩大（偏度增加）还是缩小？",
            "如果偏度是结构性的，将「典型」和「极端」群体分开进行分析。",
        ],
    },
    SignalType.LEFT_SKEWED: {
        "title": "分析 {column} 的左偏分布",
        "description": "理解 '{column}' 左偏的原因，以及是否代表低绩效风险。",
        "steps": [
            "提取 '{column}' 低于 10 分位数的记录，分析其特征。",
            "判断低值是：(a) 测量误差，(b) 特殊定价或折扣，(c) 真实的低绩效。",
            "如果是低绩效：是否集中在特定细分群体、地区或时间段？",
            "量化影响：如果将末尾绩效者提升至中位数水平，均值会变化多少？",
            "建立监控，检测低值尾部是否随时间增长。",
        ],
    },
    SignalType.HIGH_MISSING_RATE: {
        "title": "改善 {column} 的数据质量",
        "description": "调查并修复 '{column}' 的数据缺失问题，提高分析可靠性。",
        "steps": [
            "判断 '{column}' 的缺失值是随机还是系统性的（与时间、类别或其他列相关）。",
            "如果是系统性缺失：哪些细分群体或时间段受影响最大？这是已知的数据采集缺失吗？",
            "评估影响：填补缺失值是否会改变关键结论？",
            "联系数据所有者，了解数据缺失的原因以及采集流程是否可以改进。",
            "如果可以填补，测试简单策略（均值、中位数、众数）并记录所选择的方法。",
        ],
    },
    SignalType.HIGH_CARDINALITY: {
        "title": "降低 {column} 的基数以便分析",
        "description": "将 '{column}' 从高基数字段转换为可供分析的分组。",
        "steps": [
            "审查 '{column}' 的不同值——是否存在明显的分组或层级关系？",
            "检查是否存在导致唯一值虚高的近似重复值或命名不一致问题。",
            "如果 '{column}' 是标识符：将其排除在维度分析之外，仅用于关联或去重。",
            "如果 '{column}' 应为分类变量：应用分箱策略（基于频率、基于值或基于业务规则）。",
            "在用于报告之前，与领域专家验证简化后的分类。",
        ],
    },
    SignalType.LOW_VARIANCE: {
        "title": "评估 {column} 的分析价值",
        "description": "鉴于 '{column}' 区分能力较低，判断其是否应保留在分析数据集中。",
        "steps": [
            "确认低方差是真实的而非数据截断或默认值造成的人为现象。",
            "检查 '{column}' 是否预期存在变化——如果是，方差缺失本身就是一项发现。",
            "如果该列确实恒定：在细分和分析中降低其优先级。",
            "寻找能够以更细粒度衡量相同业务概念的其他指标。",
            "记录保留或排除 '{column}' 的决策依据，使后续分析人员理解原因。",
        ],
    },
}

# ---------------------------------------------------------------------------
# Alternative explanation templates (zh-CN)
# ---------------------------------------------------------------------------

_ALTERNATIVE_TEMPLATES: dict[SignalType, list[str]] = {
    SignalType.RIGHT_SKEWED: [
        "'{column}' 的分布可能存在未考虑的自然上限——检查'极端'值是否实际在正常运营范围内。",
        "右偏可能是 '{column}' 的计算方式（如从高频数据聚合）造成的人为现象，而非真实业务模式。",
    ],
    SignalType.OUTLIER_DETECTED: [
        "IQR 方法可能对 '{column}' 过于敏感——考虑使用其他异常值检测方法（z-score、MAD 或百分位法）。",
        "这些'异常值'可能代表一个合理的子群体而非异常记录——调查它们是否有共同特征。",
    ],
    SignalType.DECREASING_TREND: [
        "'{column}' 的表观下降可能是季节性而非结构性的——将分析扩展到多个季节周期。",
        "数据采集或报告方法的变化可能解释了这一趋势——核实分析期间的定义是否一致。",
    ],
    SignalType.INCREASING_TREND: [
        "'{column}' 的增长可能反映了一次性事件（并购、促销、定价变化），而非有机增长势头。",
        "趋势可能被少数异常交易夸大——检查中位数是否呈现相同模式。",
    ],
    SignalType.HIGH_CONCENTRATION: [
        "集中度可能是行业常态——在判断为风险之前，对比现有基准数据。",
        "'{column}' 的分类分组可能过于细致，造成了人为集中——尝试使用更宽泛的分组。",
    ],
}

# ---------------------------------------------------------------------------
# Cross-pattern questions (zh-CN)
# ---------------------------------------------------------------------------

_CROSS_PATTERN_QUESTIONS: dict[frozenset[SignalType], list[dict]] = {
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.RIGHT_SKEWED}): [
        {
            "question": "是否是同一组实体同时驱动了右偏和高集中度？如果是，业务在结构上依赖极少数群体。",
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.OUTLIER_DETECTED, SignalType.RIGHT_SKEWED}): [
        {
            "question": "检测到的异常值是否是右偏的原因？如果移除异常值，分布是否会变得对称？",
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.DECREASING_TREND}): [
        {
            "question": "下降是由头部贡献者价值减少驱动的，还是长尾在缩小？两种情况的应对策略根本不同。",
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_CONCENTRATION, SignalType.INCREASING_TREND}): [
        {
            "question": "增长是否集中在已经占主导地位的实体上？如果是，集中度随增长一起上升——这是复合风险。",
            "category": "cross_pattern",
        },
    ],
    frozenset({SignalType.HIGH_MISSING_RATE, SignalType.OUTLIER_DETECTED}): [
        {
            "question": "缺失数据是否可能在制造人为的异常值？如果缺失值被默认设为零或极端值，这两个信号可能共享同一根本原因。",
            "category": "cross_pattern",
        },
    ],
}


# ---------------------------------------------------------------------------
# Investigator
# ---------------------------------------------------------------------------

class InteractiveInvestigator:
    """Produces a forward-looking InteractiveInvestigationReport."""

    def investigate(
        self,
        report: InvestigationReport,
    ) -> InteractiveInvestigationReport:
        findings = report.findings

        follow_ups = self._generate_follow_up_questions(findings)
        data_gaps = self._identify_data_gaps(findings)
        paths = self._build_investigation_paths(findings)
        unresolved = self._collect_unresolved(findings)

        return InteractiveInvestigationReport(
            follow_up_questions=follow_ups,
            data_gaps=data_gaps,
            investigation_paths=paths,
            unresolved_areas=unresolved,
        )

    # -- Follow-up questions --------------------------------------------------

    def _generate_follow_up_questions(
        self,
        findings: list[Finding],
    ) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []

        for f in findings:
            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue

            related = [f.title]

            if f.status == HypothesisStatus.SUPPORTED:
                questions.extend(
                    self._drill_down_questions(signal_type, f, related)
                )
            elif f.status == HypothesisStatus.REFUTED:
                questions.extend(
                    self._alternative_questions(signal_type, f, related)
                )
            elif f.status == HypothesisStatus.INCONCLUSIVE:
                questions.extend(
                    self._inconclusive_questions(signal_type, f, related)
                )

        signal_types = {self._infer_signal_type(f) for f in findings}
        signal_types.discard(None)
        questions.extend(
            self._cross_pattern_questions(signal_types, findings)
        )

        priority_order = {"high": 0, "medium": 1, "low": 2}
        questions.sort(key=lambda q: priority_order.get(q.priority, 2))

        seen: set[str] = set()
        unique: list[FollowUpQuestion] = []
        for q in questions:
            if q.question not in seen:
                seen.add(q.question)
                unique.append(q)
        return unique

    def _drill_down_questions(
        self, signal_type: SignalType, finding: Finding, related: list[str],
    ) -> list[FollowUpQuestion]:
        templates = _DRILL_DOWN_TEMPLATES.get(signal_type, [])
        return [
            FollowUpQuestion(
                question=t["question"].format(column=self._extract_column(finding)),
                priority=self._confidence_to_priority(finding),
                category=t["category"],
                related_finding_titles=related,
                required_data=[
                    d.format(column=self._extract_column(finding))
                    for d in t.get("required_data", [])
                ],
            )
            for t in templates[:2]
        ]

    def _alternative_questions(
        self, signal_type: SignalType, finding: Finding, related: list[str],
    ) -> list[FollowUpQuestion]:
        templates = _ALTERNATIVE_TEMPLATES.get(signal_type, [])
        return [
            FollowUpQuestion(
                question=t.format(column=self._extract_column(finding)),
                priority="medium",
                category="alternative_explanation",
                related_finding_titles=related,
                required_data=[],
            )
            for t in templates[:1]
        ]

    def _inconclusive_questions(
        self, signal_type: SignalType, finding: Finding, related: list[str],
    ) -> list[FollowUpQuestion]:
        return [
            FollowUpQuestion(
                question=(
                    f"需要哪些额外数据或分析来帮助解决未确定的发现 "
                    f"'{finding.title}'？"
                ),
                priority="medium",
                category="data_gap",
                related_finding_titles=related,
                required_data=[
                    f"{self._extract_column(finding)} 的额外数据",
                    "更长时间范围或更细粒度的细分数据",
                ],
            )
        ]

    def _cross_pattern_questions(
        self, signal_types: set[SignalType], findings: list[Finding],
    ) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []
        all_titles = [f.title for f in findings]

        for key, templates in _CROSS_PATTERN_QUESTIONS.items():
            if key.issubset(signal_types):
                for t in templates:
                    questions.append(
                        FollowUpQuestion(
                            question=t["question"],
                            priority="high",
                            category=t["category"],
                            related_finding_titles=list(all_titles),
                            required_data=[],
                        )
                    )
        return questions

    # -- Data gaps ------------------------------------------------------------

    def _identify_data_gaps(self, findings: list[Finding]) -> list[DataGap]:
        gaps: list[DataGap] = []
        seen_gaps: set[str] = set()

        for f in findings:
            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue
            templates = _DATA_GAP_TEMPLATES.get(signal_type, [])
            for t in templates:
                if t["gap"] in seen_gaps:
                    continue
                seen_gaps.add(t["gap"])
                gaps.append(
                    DataGap(
                        gap=t["gap"],
                        impact=t["impact"],
                        affected_hypotheses=[f.title],
                        suggested_source=t["suggested_source"],
                    )
                )
        return gaps

    # -- Investigation paths --------------------------------------------------

    def _build_investigation_paths(
        self, findings: list[Finding],
    ) -> list[InvestigationPath]:
        paths: list[InvestigationPath] = []

        for f in findings:
            if f.status != HypothesisStatus.SUPPORTED:
                continue
            signal_type = self._infer_signal_type(f)
            if signal_type is None:
                continue
            template = _PATH_TEMPLATES.get(signal_type)
            if template is None:
                continue
            column = self._extract_column(f)
            paths.append(
                InvestigationPath(
                    title=template["title"].format(column=column),
                    description=template["description"].format(column=column),
                    steps=[s.format(column=column) for s in template["steps"]],
                    starting_finding=f.title,
                )
            )
        return paths[:5]

    # -- Unresolved areas -----------------------------------------------------

    def _collect_unresolved(self, findings: list[Finding]) -> list[str]:
        return [
            f.title
            for f in findings
            if f.status == HypothesisStatus.INCONCLUSIVE
        ]

    # -- Helpers --------------------------------------------------------------

    def _infer_signal_type(self, finding: Finding) -> SignalType | None:
        for e in finding.supporting_evidence:
            if e.supporting_signal is not None:
                return e.supporting_signal
        for e in finding.contradicting_evidence:
            if e.supporting_signal is not None:
                return e.supporting_signal
        return None

    def _extract_column(self, finding: Finding) -> str:
        for e in finding.supporting_evidence:
            if e.related_column:
                return e.related_column
        for e in finding.contradicting_evidence:
            if e.related_column:
                return e.related_column
        return "unknown_column"

    @staticmethod
    def _confidence_to_priority(finding: Finding) -> str:
        confidence = finding.confidence.value
        if confidence == "high":
            return "high"
        elif confidence == "medium":
            return "medium"
        return "low"
