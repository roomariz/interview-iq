import json
import runpy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from config import settings
from interview_app_backend.llm import client as llm
from interview_app_backend.services import evaluation_service


def test_direct_grok_configuration_preserves_openrouter_ranking():
    path = Path(__file__).resolve().parents[1] / "config" / "settings.py"
    with patch.dict("os.environ", {"LLM_PROVIDER": "grok", "GROK_MODEL": "grok-4.3"}, clear=True), patch(
        "dotenv.load_dotenv"
    ), patch("dotenv.dotenv_values", return_value={}):
        config = runpy.run_path(str(path))
    assert config["MODEL_NAME"] == "grok-4.3"
    assert config["PRIMARY_PROVIDER"] == "grok"
    assert config["OPENROUTER_MODEL_NAME"] == "google/gemma-4-31b-it:free"


@pytest.fixture
def grok(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "grok")
    client = Mock()
    getter = Mock(return_value=client)
    monkeypatch.setattr(llm, "get_grok_client", getter, raising=False)
    yield client, getter
    llm.clear_last_llm_call_metadata()


def test_service_factory_uses_xai_when_selected(grok):
    client, getter = grok
    assert llm.get_openrouter_client() is client
    getter.assert_called_once_with()


def test_question_call_uses_grok_despite_legacy_openrouter_argument(grok):
    client, _ = grok
    client.responses.create.return_value = Mock(output_text='[{"question":"How would you investigate API latency?"}]')
    output = llm.call_llm("prompt", client, task="question_generation.cv_based", provider="open-router")
    assert json.loads(output)[0]["question"].endswith("?")
    arguments = client.responses.create.call_args.kwargs
    assert arguments["model"] == settings.GROK_MODEL
    assert arguments["store"] is False
    assert llm.get_last_llm_call_metadata()["provider"] == "grok"


def test_grok_evidence_keeps_existing_pydantic_validation(grok):
    client, _ = grok
    client.responses.create.return_value = Mock(output_text='{"metrics":"not a list"}')
    with pytest.raises(RuntimeError, match="We encountered an issue"):
        llm.call_llm("prompt", client, task="evaluation.evidence_extraction")


def test_existing_evaluator_uses_direct_grok(grok, monkeypatch):
    client, _ = grok
    monkeypatch.setattr(evaluation_service, "is_answer_relevant", lambda *args: True)
    payload = {
        "evidence": {"metrics": [], "actions": ["profiled API"], "reasoning": "Reduced repeated work"},
        "scores": {key: 7 for key in ["technical_accuracy", "clarity", "relevance", "structure",
                                    "specificity", "communication", "problem_solving_approach"]},
        "strengths": ["Concrete action"], "improvement_areas": ["Quantify impact"],
        "overall_summary": "Relevant example.",
    }
    client.responses.create.side_effect = [
        Mock(output_text='{"has_reasoning":true}'), Mock(output_text=json.dumps(payload)),
    ]
    result = evaluation_service.evaluate_answer(
        "Describe a system performance improvement.", "I profiled the slow API and cached repeated database queries.",
    )
    assert "scores" in result
    assert result["evaluation_context"]["has_reasoning"] is True
    assert {call.kwargs["model"] for call in client.responses.create.call_args_list} == {settings.GROK_MODEL}


def test_grok_authentication_failure_does_not_call_openrouter(grok, monkeypatch):
    client, _ = grok
    error = RuntimeError("401 authentication failed")
    client.responses.create.side_effect = error
    fallback = Mock()
    monkeypatch.setattr(llm, "create_openrouter_client", fallback)
    with pytest.raises(RuntimeError):
        llm.call_llm("prompt", client)
    assert client.responses.create.call_count == 1
    fallback.assert_not_called()


def test_grok_request_uses_sdk_with_xai_url_and_no_response_storage(grok):
    import httpx
    from openai import OpenAI

    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(200, json={
            "id": "response-test", "object": "response", "created_at": 0,
            "status": "completed", "model": settings.GROK_MODEL,
            "output": [{"type": "message", "id": "message-test", "role": "assistant",
                        "status": "completed", "content": [{"type": "output_text", "text": "YES", "annotations": []}]}],
        })

    with OpenAI(api_key="test-key", base_url="https://api.x.ai/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        assert llm.call_llm("Relevant?", client, task="evaluation.relevance_check") == "YES"
    assert str(captured[0].url) == "https://api.x.ai/v1/responses"
    assert captured[0].headers["Authorization"] == "Bearer test-key"
    assert json.loads(captured[0].content)["store"] is False
