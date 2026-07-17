"""Prompt contract for generating the full investigation narrative (zh-CN).

Contract
--------
Version:     1.0.0
Input:       InvestigationReport (deterministic pipeline output)
Output:      Narrative (executive summary, key findings, evidence,
             business impact, recommendations)
Language:    Simplified Chinese

Traceability rules enforced by the consuming service:
1.  Every claim in key_findings MUST reference at least one piece of
    evidence from the InvestigationReport.
2.  Numeric values in the supporting_evidence_summary MUST match values
    from the source Evidence objects (no hallucinated statistics).
3.  Recommendations MUST be drawn from the report's next_steps list.
4.  The executive_summary MUST state the overall risk and confidence
    levels from the report's ExecutiveSummary.

Provider notes
--------------
This prompt is PROVIDER-AGNOSTIC.  It works with any LLM that accepts
system + user messages.
"""

PROMPT_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# System prompt — sets the role, tone, and output contract
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
你是一名调查数据分析师，负责从确定性分析报告中生成结构化的调查报告。

你的输出必须：
- **基于证据**：每一项声明都必须引用输入报告中的具体指标或发现。
- **与业务相关**：解释每个发现为什么重要，而不仅仅是发现是什么。
- **诚实对待不确定性**：区分已确认的模式（支持的假设）、已被否定的假设（被驳回的假设）和有待进一步研究的问题（未确定的假设）。
- **可执行**：每项建议都应足够具体，让业务相关人员知道下一步该做什么。

不要：
- 编造输入报告中不存在的统计数据。
- 在没有证据支持的情况下将相关性表述为因果关系。
- 超越数据支持的边界进行推测。

请使用简体中文输出所有内容。你将收到结构化的调查报告 JSON，请按照提供的 schema 生成结构化分析结果。
"""

# ---------------------------------------------------------------------------
# User message — the templated prompt that carries the report data
# ---------------------------------------------------------------------------

USER_MESSAGE_TEMPLATE = """\
请分析以下调查报告并生成结构化叙事。

## 调查报告 (JSON)

{report_json}

## 说明

1.  **执行摘要**：综合整体调查情况。说明总共测试了多少假设，其中多少被支持 / 驳回 / 未确定，整体风险等级（{overall_risk}）和置信度（{overall_confidence}）。突出最重要的 2-3 个发现。

2.  **关键发现**：对报告中的每个发现，撰写简洁的总结，说明：
    - 发现了什么（观察）
    - 证据是支持还是否定了它（状态）
    - 我们的置信度如何（置信度等级）

3.  **支持证据**：提供支持关键发现的证据的叙事性总结。在能够增强论证力度的地方引用具体指标和数值。如果证据存在矛盾或不确定性，请如实说明。

4.  **业务影响**：解释这些发现为什么重要。描述它们所代表的风险和机会。优先考虑高置信度且状态为"已支持"的发现。

5.  **建议**：列出按优先级排序的下一步行动。每项建议应具体、可执行，并可追溯到报告中的某个发现。

## 输出格式

请以匹配以下 schema 的 JSON 对象格式输出：

{output_schema}
"""


def build_user_message(
    report_json: str,
    overall_risk: str,
    overall_confidence: str,
    output_schema: str,
) -> str:
    """Render the user message template with concrete values.

    Args:
        report_json:  The InvestigationReport serialised to JSON.
        overall_risk:  From ExecutiveSummary.overall_risk.
        overall_confidence:  From ExecutiveSummary.overall_confidence.
        output_schema:  JSON Schema for the Narrative model.

    Returns:
        The filled user message, ready to send to an LLM.
    """
    return USER_MESSAGE_TEMPLATE.format(
        report_json=report_json,
        overall_risk=overall_risk,
        overall_confidence=overall_confidence,
        output_schema=output_schema,
    )
