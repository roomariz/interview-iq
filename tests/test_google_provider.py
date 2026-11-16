import json
import runpy
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from openai import OpenAI

from config import settings
from interview_app_backend.llm import client as llm
from interview_app_backend.llm import provider_clients
from interview_app_backend.services import evaluation_service


def test_google_configuration_uses_separate_model_and_preserves_openrouter():
    path = Path(__file__).resolve().parents[1] / "config" / "settings.py"
    with patch.dict("os.environ", {"LLM_PROVIDER": "google", "GOOGLE_MODEL": "gemini-3.5-flash-lite"}, clear=True), patch(
        "dotenv.load_dotenv"
    ), patch("dotenv.dotenv_values", return_value={}):
        config = runpy.run_path(str(path))
    assert config["MODEL_NAME"] == "gemini-3.5-flash-lite"
    assert config["PRIMARY_PROVIDER"] == "google"
    assert config["OPENROUTER_MODEL_NAME"] == "google/gemma-4-31b-it:free"


@pytest.fixture
def google(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "google")
    client = Mock()
    monkeypatch.setattr(llm, "get_google_client", Mock(return_value=client))
    yield client
    llm.clear_last_llm_call_metadata()


def completion(content, finish_reason="stop"):
    return Mock(choices=[Mock(message=Mock(content=content), finish_reason=finish_reason)])


def test_google_factory_uses_documented_endpoint():
    with patch.object(provider_clients, "OpenAI") as factory:
        provider_clients.create_google_client("test-key")
    factory.assert_called_once_with(api_key="test-key", base_url="https://generativelanguage.googleapis.com/v1beta/openai/")


def test_service_factory_selects_google(google):
    assert llm.get_openrouter_client() is google


def test_question_call_overrides_legacy_openrouter_argument(google):
    google.chat.completions.create.return_value = completion('{"questions":[]}')
    result = llm.call_llm("JSON question prompt", google, provider="open-router", task="question_generation.cv_based")
    assert json.loads(result) == {"questions": []}
    arguments = google.chat.completions.create.call_args.kwargs
    assert arguments["model"] == settings.GOOGLE_MODEL
    assert arguments["messages"] == [{"role": "user", "content": "JSON question prompt"}]
    assert arguments["response_format"]["type"] == "json_schema"
    schema = arguments["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["questions"]["minItems"] == 5
    assert schema["properties"]["questions"]["maxItems"] == 5
    google.responses.create.assert_not_called()
    assert llm.get_last_llm_call_metadata()["provider"] == "google"


@pytest.mark.parametrize("content,finish", [(None, "stop"), ("partial", "length"), ("", "content_filter")])
def test_empty_or_truncated_google_responses_fail(google, content, finish):
    google.chat.completions.create.return_value = completion(content, finish)
    with pytest.raises(RuntimeError):
        llm.call_llm("prompt", google)


@pytest.mark.parametrize("payload", ["invalid JSON", '{"scores":{"relevance":7}}'])
def test_google_scoring_keeps_pydantic_validation(google, payload):
    google.chat.completions.create.return_value = completion(payload)
    with pytest.raises(RuntimeError):
        llm.call_llm("JSON scoring prompt", google, task="evaluation.scoring")


def test_existing_evidence_service_uses_google_chat(google):
    google.chat.completions.create.return_value = completion('{"has_reasoning":true}')
    context = evaluation_service.extract_evidence_context("How did you improve performance?", "I profiled the API.")
    assert context["has_reasoning"] is True
    assert google.chat.completions.create.call_args.kwargs["response_format"] == {"type": "json_object"}


def test_plain_text_google_relevance_request(google):
    google.chat.completions.create.return_value = completion("YES")
    assert llm.call_llm("Relevant?", google, task="evaluation.relevance_check", temperature=0) == "YES"
    assert "response_format" not in google.chat.completions.create.call_args.kwargs


def test_google_auth_error_has_no_implicit_paid_fallback(google, monkeypatch):
    google.chat.completions.create.side_effect = RuntimeError("403 permission denied")
    fallback = Mock()
    monkeypatch.setattr(llm, "create_openrouter_client", fallback)
    with pytest.raises(RuntimeError):
        llm.call_llm("prompt", google)
    assert google.chat.completions.create.call_count == 1
    fallback.assert_not_called()


def test_real_sdk_uses_google_chat_endpoint_with_mocked_http(google):
    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(200, json={
            "id": "completion-test", "object": "chat.completion", "created": 0,
            "model": settings.GOOGLE_MODEL,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "YES"}}],
        })

    with OpenAI(api_key="test-key", base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        assert llm.call_llm("Relevant?", client, task="evaluation.relevance_check") == "YES"
    assert str(captured[0].url) == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert captured[0].headers["Authorization"] == "Bearer test-key"


def test_openrouter_google_models_still_use_responses_api(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "open-router")
    client = Mock()
    client.responses.create.return_value = Mock(output_text="OpenRouter answer")
    assert llm.call_llm("prompt", client) == "OpenRouter answer"
    client.chat.completions.create.assert_not_called()


def test_missing_google_key_is_reported_before_a_request(monkeypatch):
    monkeypatch.setattr(provider_clients, "GOOGLE_API_KEY", "")
    with pytest.raises(ValueError, match="GOOGLE_API_KEY is not set"):
        provider_clients.get_google_client()


@pytest.mark.parametrize("failure", ["rate_limit", "timeout"])
def test_google_transient_errors_have_bounded_retries(google, monkeypatch, failure):
    from openai import APITimeoutError, RateLimitError

    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
    error = APITimeoutError(request=request) if failure == "timeout" else RateLimitError(
        "quota exceeded", response=httpx.Response(429, request=request), body={"error": "quota exceeded"},
    )
    monkeypatch.setattr(llm.time, "sleep", Mock())
    google.chat.completions.create.side_effect = error
    with pytest.raises(RuntimeError):
        llm.call_llm("prompt", google)
    assert google.chat.completions.create.call_count == 3


def test_existing_google_scoring_workflow(google, monkeypatch):
    monkeypatch.setattr(evaluation_service, "is_answer_relevant", lambda *args: True)
    evaluation = {
        "evidence": {"metrics": [], "actions": ["profiled API"], "reasoning": "Reduced repeated work"},
        "scores": {key: 7 for key in ["technical_accuracy", "clarity", "relevance", "structure",
                                    "specificity", "communication", "problem_solving_approach"]},
        "strengths": ["Concrete action"], "improvement_areas": ["Quantify impact"],
        "overall_summary": "Relevant example.",
    }
    google.chat.completions.create.side_effect = [completion('{"has_reasoning":true}'), completion(json.dumps(evaluation))]
    result = evaluation_service.evaluate_answer("How did you improve performance?", "I profiled the API and cached repeated queries.")
    assert result["evaluation_context"]["has_reasoning"] is True
    assert "scores" in result
