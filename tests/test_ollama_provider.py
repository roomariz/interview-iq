import json
from unittest.mock import Mock

import pytest
import requests

from config import settings
from interview_app_backend.llm import client as llm
from interview_app_backend.llm import ollama_client as ollama


@pytest.fixture
def cloud(monkeypatch):
    values = {
        "LLM_PROVIDER": "ollama", "OLLAMA_API_KEY": "test-key",
        "OLLAMA_MODEL": "gemma4:cloud", "OLLAMA_HOST": "https://ollama.com",
        "OLLAMA_FALLBACK_TO_OPENROUTER": False, "MODEL_NAME": "gemma4:cloud",
    }
    for name, value in values.items():
        monkeypatch.setattr(settings, name, value)
    post = Mock()
    monkeypatch.setattr(ollama.requests, "post", post)
    monkeypatch.setattr(ollama.time, "sleep", Mock())
    llm.clear_last_llm_call_metadata()
    yield post
    llm.clear_last_llm_call_metadata()


def response(text="answer", status=200, **fields):
    return Mock(status_code=status, json=Mock(return_value={
        "message": {"content": text}, "done": True, **fields,
    }))


def test_documented_cloud_request_and_alias(cloud):
    cloud.return_value = response()
    result = llm.call_llm("prompt", llm.get_openrouter_client(), temperature=0, task="evaluation.reference_answer")
    assert result == "answer"
    arguments = cloud.call_args.kwargs
    assert cloud.call_args.args == ("https://ollama.com/api/chat",)
    assert arguments["headers"] == {"Authorization": "Bearer test-key"}
    assert arguments["json"] == {
        "model": "gemma4:31b", "messages": [{"role": "user", "content": "prompt"}],
        "stream": False, "options": {"temperature": 0},
    }
    assert arguments["timeout"] == settings.LLM_TIMEOUT
    assert arguments["allow_redirects"] is False
    assert llm.get_last_llm_call_metadata()["provider"] == "ollama"
    assert llm.get_last_llm_call_metadata()["model"] == "gemma4:31b"


def test_custom_model_is_preserved(cloud, monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "custom:large")
    cloud.return_value = response("YES")
    assert llm.call_llm("prompt", llm.get_openrouter_client(), task="evaluation.relevance_check") == "YES"
    assert cloud.call_args.kwargs["json"]["model"] == "custom:large"


@pytest.mark.parametrize("status,attempts,reason", [
    (401, 1, "authentication_failed"), (403, 1, "authentication_failed"),
    (404, 1, "http_404"), (400, 1, "http_400"), (429, 2, "rate_limited"), (503, 2, "http_503"),
])
def test_http_failures_are_bounded_and_never_fall_back_implicitly(cloud, monkeypatch, status, attempts, reason):
    cloud.return_value = response(status=status)
    openrouter = Mock()
    monkeypatch.setattr(llm, "create_openrouter_client", openrouter)
    with pytest.raises(RuntimeError, match=reason):
        llm.call_llm("prompt", llm.get_openrouter_client())
    assert cloud.call_count == attempts
    openrouter.assert_not_called()


@pytest.mark.parametrize("error,reason", [(requests.Timeout("secret"), "timeout"), (requests.ConnectionError("secret"), "connection_failed")])
def test_transport_errors_do_not_leak_details(cloud, error, reason):
    cloud.side_effect = error
    with pytest.raises(RuntimeError, match=reason) as caught:
        llm.call_llm("prompt", llm.get_openrouter_client())
    assert "secret" not in str(caught.value)
    assert cloud.call_count == 2


def test_retry_can_recover_from_rate_limit(cloud):
    cloud.side_effect = [response(status=429), response()]
    assert llm.call_llm("prompt", llm.get_openrouter_client()) == "answer"
    assert cloud.call_count == 2


@pytest.mark.parametrize("text", ["not json", '{"scores":{"relevance":9}}', "", "null"])
def test_invalid_evaluations_are_rejected(cloud, text):
    cloud.return_value = response(text)
    with pytest.raises(RuntimeError, match="invalid_json_or_schema"):
        llm.call_llm("prompt", llm.get_openrouter_client(), task="evaluation.scoring")
    assert cloud.call_count == 2


def test_evidence_schema_and_json_retry(cloud):
    valid = json.dumps({"has_reasoning": True, "metrics": []})
    cloud.side_effect = [response('{"metrics":"invalid"}'), response(valid)]
    assert llm.call_llm("prompt", llm.get_openrouter_client(), task="evaluation.evidence_extraction") == valid
    assert cloud.call_count == 2
    assert "format" not in cloud.call_args.kwargs["json"]
    assert cloud.call_args.kwargs["json"]["messages"][0]["role"] == "system"


@pytest.mark.parametrize("fields", [{"done": False}, {"error": "test-key"}])
def test_incomplete_or_error_envelope_is_rejected(cloud, fields):
    cloud.return_value = response(**fields)
    with pytest.raises(RuntimeError, match="invalid_json_or_schema"):
        llm.call_llm("prompt", llm.get_openrouter_client())
    assert cloud.call_count == 2


def test_explicit_fallback_uses_existing_openrouter_ranking(cloud, monkeypatch):
    cloud.return_value = response(status=401)
    monkeypatch.setattr(settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "fallback-key")
    openrouter = Mock()
    openrouter.responses.create.side_effect = [RuntimeError("404 no endpoints available"), Mock(output_text="fallback answer")]
    factory = Mock(return_value=openrouter)
    monkeypatch.setattr(llm, "create_openrouter_client", factory)
    assert llm.call_llm("prompt", llm.get_openrouter_client()) == "fallback answer"
    factory.assert_called_once_with("fallback-key")
    assert [c.kwargs["model"] for c in openrouter.responses.create.call_args_list] == settings.FALLBACK_CHAIN[:2]
    assert llm.get_last_llm_call_metadata()["model"] == settings.FALLBACK_CHAIN[1]


def test_enabled_fallback_still_requires_openrouter_credentials(cloud, monkeypatch):
    cloud.return_value = response(status=401)
    monkeypatch.setattr(settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "")
    with pytest.raises(RuntimeError, match="OpenRouter fallback requires"):
        llm.call_llm("prompt", llm.get_openrouter_client())


@pytest.mark.parametrize("field,value,reason", [
    ("OLLAMA_API_KEY", "", "OLLAMA_API_KEY"),
    ("OLLAMA_HOST", "http://localhost:11434", "OLLAMA_HOST"),
    ("OLLAMA_HOST", "https://other.example", "OLLAMA_HOST"),
    ("OLLAMA_MODEL", "", "OLLAMA_MODEL"),
    ("LLM_TIMEOUT", 0, "LLM_TIMEOUT"),
])
def test_invalid_configuration_makes_no_request(cloud, monkeypatch, field, value, reason):
    monkeypatch.setattr(settings, field, value)
    with pytest.raises(RuntimeError, match=reason):
        llm.call_llm("prompt", llm.get_openrouter_client())
    cloud.assert_not_called()


def test_cancellation_never_falls_back(cloud, monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    with pytest.raises(RuntimeError, match="cancelled"):
        llm.call_llm("prompt", llm.get_openrouter_client(), should_abort=lambda: True)
    cloud.assert_not_called()


def test_switch_back_to_openrouter_uses_existing_factory(cloud, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "open-router")
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "openrouter-key")
    factory = Mock(return_value=Mock())
    monkeypatch.setattr(llm, "create_openrouter_client", factory)
    assert llm.get_openrouter_client() is factory.return_value
    factory.assert_called_once_with("openrouter-key")
    cloud.assert_not_called()


def test_invalid_json_can_fall_back_only_when_enabled(cloud, monkeypatch):
    cloud.return_value = response("invalid JSON")
    monkeypatch.setattr(settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "fallback-key")
    openrouter = Mock()
    openrouter.responses.create.return_value = Mock(output_text='{"has_reasoning": true}')
    monkeypatch.setattr(llm, "create_openrouter_client", Mock(return_value=openrouter))
    result = llm.call_llm("prompt", llm.get_openrouter_client(), task="evaluation.evidence_extraction")
    assert json.loads(result)["has_reasoning"] is True
    assert cloud.call_count == 2
    assert llm.get_last_llm_call_metadata()["provider"] != "ollama"


def test_invalid_prompt_makes_no_request(cloud):
    with pytest.raises(RuntimeError, match="Invalid LLM prompt"):
        llm.call_llm("\x00", llm.get_openrouter_client())
    cloud.assert_not_called()


def test_network_guard_blocks_external_connections():
    import socket

    with socket.socket() as connection, pytest.raises(RuntimeError, match="External network"):
        connection.connect(("203.0.113.1", 443))
