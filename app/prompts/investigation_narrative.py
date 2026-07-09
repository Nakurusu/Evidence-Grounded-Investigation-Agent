"""Prompt contract for generating the full investigation narrative.

Contract
--------
Version:     1.0.0
Input:       InvestigationReport (deterministic pipeline output)
Output:      Narrative (executive summary, key findings, evidence,
             business impact, recommendations)

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
system + user messages.  Provider-specific formatting (e.g., Anthropic's
system prompt vs OpenAI's system message) is handled by the narrative
generator service, not by this contract.
"""

PROMPT_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# System prompt — sets the role, tone, and output contract
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an investigative data analyst producing a structured investigation \
narrative from a deterministic analysis report.

Your output must be:
- **Evidence-based**: every claim references specific metrics or findings \
from the input report.
- **Business-relevant**: explain WHY each finding matters, not just WHAT \
was found.
- **Honest about uncertainty**: distinguish between confirmed patterns \
(supported hypotheses), disproven assumptions (refuted hypotheses), and \
open questions (inconclusive hypotheses).
- **Actionable**: every recommendation should be specific enough that a \
business stakeholder knows what to do next.

Do NOT:
- Invent statistics not present in the input report.
- State correlations as causations without evidence.
- Speculate beyond what the data supports.

You will receive the investigation report as structured JSON.  Produce \
your analysis as structured output following the exact schema provided.
"""

# ---------------------------------------------------------------------------
# User message — the templated prompt that carries the report data
# ---------------------------------------------------------------------------

USER_MESSAGE_TEMPLATE = """\
Analyse the following investigation report and produce a structured \
narrative.

## Investigation Report (JSON)

{report_json}

## Instructions

1.  **Executive Summary**: Synthesise the overall investigation.  State \
the total hypotheses tested, how many were supported / refuted / \
inconclusive, the overall risk level ({overall_risk}), and confidence \
({overall_confidence}).  Highlight the 2-3 most important findings.

2.  **Key Findings**: For each finding in the report, produce a concise \
summary that states:
    - What was found (the observation)
    - Whether evidence supports or refutes it (the status)
    - How confident we are (the confidence level)

3.  **Supporting Evidence**: Provide a narrative summary of the evidence \
supporting the key findings.  Reference specific metrics and values \
where they strengthen the argument.  If evidence is contradictory or \
inconclusive, say so.

4.  **Business Impact**: Explain why these findings matter.  Describe \
the risks and opportunities they represent.  Prioritise findings with \
HIGH confidence and SUPPORTED status.

5.  **Recommendations**: List prioritised next steps.  Each \
recommendation should be specific, actionable, and traceable to a \
finding in the report.

## Output Format

Produce your response as a JSON object matching this schema:

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
        output_schema:  JSON Schema for the Narrative model (used to
                        instruct the LLM about the expected output format).

    Returns:
        The filled user message, ready to send to an LLM.
    """
    return USER_MESSAGE_TEMPLATE.format(
        report_json=report_json,
        overall_risk=overall_risk,
        overall_confidence=overall_confidence,
        output_schema=output_schema,
    )
