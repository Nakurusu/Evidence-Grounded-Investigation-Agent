"""Prompt contract for generating an executive brief.

Contract
--------
Version:     1.0.0
Input:       InvestigationReport (deterministic pipeline output)
Output:      Narrative (shorter, stakeholder-facing format)

This prompt produces a more concise narrative than the full investigation
narrative.  It is designed for stakeholders who need the key takeaways
without the detailed evidence walkthrough.

Traceability rules:
1.  The executive_summary MUST include overall risk and confidence.
2.  key_findings MUST be ranked by priority (HIGH confidence first).
3.  Recommendations MUST be the top 3-5 most impactful actions.
4.  No invented statistics.

Provider notes
--------------
Provider-agnostic.  See investigation_narrative.py for the full rationale.
"""

PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = """\
You are an investigative data analyst producing an executive brief from a \
deterministic analysis report.

Your output must be:
- **Concise**: stakeholders need the key takeaways, not every detail.
- **Business-focused**: emphasise impact, risk, and recommended actions.
- **Honest**: distinguish confirmed findings from open questions.

Do NOT invent statistics.  Do NOT state correlations as causations.

You will receive the investigation report as structured JSON.  Produce \
your analysis as structured output following the exact schema provided.
"""

USER_MESSAGE_TEMPLATE = """\
Produce an executive brief from the following investigation report.

## Investigation Report (JSON)

{report_json}

## Instructions

1.  **Executive Summary**: 2-3 sentences covering what was investigated, \
the overall risk level ({overall_risk}), and the most critical finding.

2.  **Key Findings**: The top 3-5 findings, one sentence each.  State \
the finding, status (supported / refuted), and confidence.

3.  **Supporting Evidence**: A single paragraph summarising the \
strongest evidence behind the top findings.

4.  **Business Impact**: A single paragraph on what these findings mean \
for the business — the key risks and/or opportunities.

5.  **Recommendations**: The top 3-5 next steps, prioritised by impact.

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
    """Render the user message template with concrete values."""
    return USER_MESSAGE_TEMPLATE.format(
        report_json=report_json,
        overall_risk=overall_risk,
        overall_confidence=overall_confidence,
        output_schema=output_schema,
    )
