"""LLMNarrativeGenerator — OpenAI-compatible narrative generation (Phase 7).

Implements the NarrativeGenerator Protocol using the OpenAI SDK.
Works with any OpenAI-compatible API endpoint: OpenAI, Anthropic (via proxy),
local models (vLLM, Ollama, etc.).

Architecture
------------
LLMNarrativeGenerator  implements the  NarrativeGenerator  Protocol.
The pipeline depends on the Protocol — it never imports this module directly.
Switching between Mock / OpenAI / future providers is a config change
(LLM_MODE), not a code change.
"""

import json
import re
from datetime import datetime, UTC

from openai import OpenAI

from app.schemas.investigation_report import InvestigationReport
from app.schemas.ai_report import Narrative, ModelMetadata
from app.prompts.investigation_narrative import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_user_message,
)
from app.core.logger import logger

# ---------------------------------------------------------------------------
# JSON extraction — LLMs often wrap JSON in markdown code fences
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def _extract_json(text: str) -> str:
    """Extract a JSON object from text that may contain markdown fences.

    Tries:
    1.  A ```json ... ``` code block.
    2.  The first { ... } span in the text.
    3.  Returns the raw text if neither matched.
    """
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()

    # Find first { and its matching }
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

    return text.strip()


# ---------------------------------------------------------------------------
# LLMNarrativeGenerator
# ---------------------------------------------------------------------------


class LLMNarrativeGenerator:
    """Generate investigation narratives using an OpenAI-compatible LLM."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        max_retries: int = 1,
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._max_tokens = max_tokens
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Public API (NarrativeGenerator Protocol)
    # ------------------------------------------------------------------

    def generate(
        self,
        report: InvestigationReport,
    ) -> tuple[Narrative, ModelMetadata]:
        """Generate a narrative from a deterministic investigation report.

        Args:
            report: The complete pipeline output.

        Returns:
            A (Narrative, ModelMetadata) pair.

        Raises:
            ValueError: If the LLM response cannot be parsed after retries.
        """
        es = report.executive_summary
        report_json = report.model_dump_json()
        output_schema = json.dumps(Narrative.model_json_schema())

        user_message = build_user_message(
            report_json=report_json,
            overall_risk=es.overall_risk,
            overall_confidence=es.overall_confidence,
            output_schema=output_schema,
        )

        narrative = self._call_with_retry(user_message)

        metadata = ModelMetadata(
            provider="openai",
            model_name=self._model,
            prompt_version=PROMPT_VERSION,
            generated_at=datetime.now(UTC),
        )

        return narrative, metadata

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_with_retry(self, user_message: str) -> Narrative:
        """Call the LLM, retrying once if JSON parsing fails."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response_text = self._call_api(user_message)
                narrative_dict = json.loads(_extract_json(response_text))
                return Narrative(**narrative_dict)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = exc
                logger.warning(
                    f"LLM response parse failed (attempt {attempt + 1}): {exc}"
                )
                if attempt < self._max_retries:
                    user_message = (
                        f"{user_message}\n\n"
                        f"IMPORTANT: Your previous response was not valid JSON. "
                        f"Please output ONLY a valid JSON object — no markdown "
                        f"fences, no extra text."
                    )

        raise ValueError(
            f"Failed to parse LLM response as Narrative after "
            f"{self._max_retries + 1} attempt(s): {last_error}"
        )

    def _call_api(self, user_message: str) -> str:
        """Send a chat completion request and return the text response."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=self._max_tokens,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")
        return content
