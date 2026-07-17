"""Prompt contract for generating an executive brief (zh-CN).

Contract
--------
Version:     1.0.0
Input:       InvestigationReport (deterministic pipeline output)
Output:      Narrative (shorter, stakeholder-facing format)
Language:    Simplified Chinese
"""

PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = """\
你是一名调查数据分析师，负责从确定性分析报告中生成高管简报。

你的输出必须：
- **简洁**：决策者需要关键结论，不需要逐一罗列细节。
- **以业务为导向**：强调影响、风险和建议行动。
- **诚实**：区分已确认的发现和尚待解决的问题。

不要编造统计数据。不要将相关性表述为因果关系。

请使用简体中文输出所有内容。你将收到结构化的调查报告 JSON，请按照提供的 schema 生成结构化分析结果。
"""

USER_MESSAGE_TEMPLATE = """\
请根据以下调查报告生成高管简报。

## 调查报告 (JSON)

{report_json}

## 说明

1.  **执行摘要**：2-3 句话，涵盖调查范围、整体风险等级（{overall_risk}）以及最关键的发现。

2.  **关键发现**：排名前 3-5 的发现，每个发现一句话。说明发现内容、状态（已支持 / 已驳回）和置信度。

3.  **支持证据**：用一段话总结支持重要发现的最有力证据。

4.  **业务影响**：用一段话说明这些发现对业务意味着什么——主要风险和/或机会。

5.  **建议**：按影响力排序的 3-5 项最重要的后续行动。

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
    return USER_MESSAGE_TEMPLATE.format(
        report_json=report_json,
        overall_risk=overall_risk,
        overall_confidence=overall_confidence,
        output_schema=output_schema,
    )
