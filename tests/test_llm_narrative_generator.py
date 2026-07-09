"""Tests for app/services/llm_narrative_generator.py."""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.llm_narrative_generator import (
    _extract_json,
    LLMNarrativeGenerator,
)
from app.schemas.ai_report import Narrative
from app.schemas.investigation_report import (
    InvestigationReport,
    ExecutiveSummary,
    DatasetSummary,
    Finding,
)
from app.models.enums import HypothesisStatus, HypothesisConfidence


# ═══════════════════════════════════════════════════════════════════════
# JSON extraction
# ═══════════════════════════════════════════════════════════════════════


class TestExtractJson:
    def test_bare_json(self):
        text = '{"key": "value"}'
        assert _extract_json(text) == '{"key": "value"}'

    def test_markdown_json_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert _extract_json(text) == '{"key": "value"}'

    def test_markdown_no_lang_fence(self):
        text = '```\n{"key": "value"}\n```'
        assert _extract_json(text) == '{"key": "value"}'

    def test_json_amidst_text(self):
        text = 'Here is the result: {"key": "value"}.  Hope it helps.'
        assert _extract_json(text) == '{"key": "value"}'

    def test_nested_json(self):
        text = '```json\n{"outer": {"inner": [1, 2, 3]}, "flag": true}\n```'
        assert _extract_json(text) == '{"outer": {"inner": [1, 2, 3]}, "flag": true}'

    def test_no_json_returns_raw(self):
        text = "plain text without any json"
        assert _extract_json(text) == "plain text without any json"


# ═══════════════════════════════════════════════════════════════════════
# Narrative generation with mocked API
# ═══════════════════════════════════════════════════════════════════════


def _minimal_report() -> InvestigationReport:
    return InvestigationReport(
        executive_summary=ExecutiveSummary(
            total_hypotheses=2,
            supported_count=2,
            refuted_count=0,
            inconclusive_count=0,
            highest_priority_findings=["Revenue concentration risk"],
            overall_risk="medium",
            overall_confidence="high",
        ),
        dataset_summary=DatasetSummary(
            row_count=100, column_count=4,
            numeric_columns=["revenue"], categorical_columns=["region"],
            datetime_columns=["date"], text_columns=[], boolean_columns=[],
        ),
        findings=[
            Finding(
                title="Revenue concentration risk",
                observation="Top customer accounts for 75% of revenue",
                status=HypothesisStatus.SUPPORTED,
                confidence=HypothesisConfidence.HIGH,
                supporting_evidence=[],
                contradicting_evidence=[],
                analysis="High dependency on few customers",
                business_impact="Revenue is fragile if top customers churn",
                recommendation="Diversify customer base",
            ),
        ],
        next_steps=["Diversify customer base", "Monitor top accounts monthly"],
    )


def _mock_narrative_json() -> dict:
    return {
        "executive_summary": "Two hypotheses tested, both supported. Revenue concentration is the key risk.",
        "key_findings": [
            "Revenue is highly concentrated in a small number of customers."
        ],
        "supporting_evidence_summary": "The top customer accounts for 75% of total revenue.",
        "business_impact_summary": "The business is vulnerable to the loss of any top customer.",
        "recommendations": [
            "Diversify customer base",
            "Monitor top accounts monthly",
        ],
    }


class TestLLMNarrativeGenerator:
    def test_generate_returns_narrative_and_metadata(self):
        gen = LLMNarrativeGenerator(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(_mock_narrative_json())))
        ]

        with patch.object(gen._client.chat.completions, "create", return_value=mock_response):
            narrative, metadata = gen.generate(_minimal_report())

        assert isinstance(narrative, Narrative)
        assert len(narrative.executive_summary) > 0
        assert len(narrative.key_findings) == 1
        assert len(narrative.recommendations) == 2
        assert metadata.provider == "openai"
        assert metadata.model_name == "gpt-4o"
        assert metadata.prompt_version is not None

    def test_handles_markdown_wrapped_response(self):
        gen = LLMNarrativeGenerator(api_key="sk-test")

        wrapped = f"```json\n{json.dumps(_mock_narrative_json())}\n```"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=wrapped))
        ]

        with patch.object(gen._client.chat.completions, "create", return_value=mock_response):
            narrative, _ = gen.generate(_minimal_report())

        assert isinstance(narrative, Narrative)

    def test_retries_on_bad_json(self):
        gen = LLMNarrativeGenerator(api_key="sk-test", max_retries=1)

        bad = "this is not json"
        good = json.dumps(_mock_narrative_json())
        mock_response_bad = MagicMock()
        mock_response_bad.choices = [MagicMock(message=MagicMock(content=bad))]
        mock_response_good = MagicMock()
        mock_response_good.choices = [MagicMock(message=MagicMock(content=good))]

        with patch.object(gen._client.chat.completions, "create", side_effect=[mock_response_bad, mock_response_good]) as mock_create:
            narrative, _ = gen.generate(_minimal_report())
            assert isinstance(narrative, Narrative)
            assert mock_create.call_count == 2

    def test_raises_after_exhausting_retries(self):
        gen = LLMNarrativeGenerator(api_key="sk-test", max_retries=0)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not json at all"))]

        with patch.object(gen._client.chat.completions, "create", return_value=mock_response):
            with pytest.raises(ValueError, match="Failed to parse"):
                gen.generate(_minimal_report())

    def test_custom_base_url_and_model(self):
        gen = LLMNarrativeGenerator(
            api_key="sk-test",
            base_url="https://custom.example.com/v1",
            model="claude-sonnet-5",
        )

        assert gen._model == "claude-sonnet-5"

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(_mock_narrative_json())))
        ]

        with patch.object(gen._client.chat.completions, "create", return_value=mock_response):
            _, metadata = gen.generate(_minimal_report())

        assert metadata.model_name == "claude-sonnet-5"
        assert metadata.provider == "openai"
