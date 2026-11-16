import httpx
import pytest

from interview_app_frontend.services.api_client import BackendError, InterviewAPIClient
from shared.api_contracts import ContextResponse


def make_client(handler):
    return InterviewAPIClient(secret="test-secret", transport=httpx.MockTransport(handler))


def test_question_posts_once_with_server_auth_and_validates_count():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer test-secret"
        return httpx.Response(200, json={"questions": [{"question": "How would you investigate service latency?"}], "meta": {}})

    result = make_client(handler).question(role="Engineer")
    assert len(result["questions"]) == 1
    assert len(calls) == 1
    with pytest.raises(BackendError, match="incomplete"):
        make_client(handler).question(role="Engineer", question_list_count=2)


@pytest.mark.parametrize("status", [301, 401, 413, 422, 429, 500, 502, 503, 504])
def test_status_errors_do_not_expose_backend_body_or_retry(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, text="private answer prompt secret", headers={"Location": "https://untrusted.invalid"})

    with pytest.raises(BackendError) as error:
        make_client(handler).question(role="Engineer")
    assert "private" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize("error", [httpx.ConnectError("private"), httpx.ReadTimeout("private")])
def test_network_failures_are_friendly(error):
    def handler(request):
        raise error
    with pytest.raises(BackendError) as caught:
        make_client(handler).question(role="Engineer")
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("result", [httpx.Response(200, text="not-json"), httpx.Response(200, json={"questions": []}),
                                    httpx.Response(200, content=b"x" * 1048577)])
def test_invalid_success_responses_are_rejected(result):
    with pytest.raises(BackendError, match="invalid response"):
        make_client(lambda request: result).question(role="Engineer")


def test_insecure_remote_urls_and_missing_secret_are_rejected():
    with pytest.raises(BackendError, match="HTTPS"):
        InterviewAPIClient(base_url="http://remote.invalid", secret="s")
    with pytest.raises(BackendError, match="configured"):
        InterviewAPIClient(secret="").question(role="Engineer")


def test_environment_configuration_is_supported(monkeypatch):
    monkeypatch.setenv("BACKEND_API_URL", "https://backend.example")
    monkeypatch.setenv("BACKEND_API_SECRET", "server-only")
    monkeypatch.setenv("BACKEND_API_TIMEOUT", "23")
    client = InterviewAPIClient()
    assert client.base_url == "https://backend.example"
    assert client.timeout == 23
    assert client.secret == "server-only"


def test_streamlit_secrets_configuration_is_supported(monkeypatch):
    import streamlit as st
    for name in ("BACKEND_API_URL", "BACKEND_API_SECRET", "BACKEND_API_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(st, "secrets", {"BACKEND_API_URL": "https://backend.example", "BACKEND_API_SECRET": "server-only"})
    client = InterviewAPIClient()
    assert client.secret == "server-only"
    assert client.base_url == "https://backend.example"


def test_context_response_requires_profile_and_limits():
    with pytest.raises(ValueError):
        ContextResponse.model_validate({"tech_stack": []})
