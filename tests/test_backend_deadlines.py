"""Wall-clock deadlines, nested operations and transport retry boundaries."""

import time
from threading import Event
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.security import InterviewSecurity
from interview_app_backend.llm import client, deadline, provider_fallback


@pytest.fixture
def budget():
    value = deadline.Deadline(time.monotonic() + 0.12)
    token = deadline.current_deadline.set(value)
    yield value
    value.cancelled.set()
    deadline.current_deadline.reset(token)


def test_nested_operations_share_budget(budget):
    first = deadline.remaining(60)
    deadline.provider_call(lambda: time.sleep(0.03), 60)
    assert 0 < deadline.remaining(60) < first
    with pytest.raises(deadline.DeadlineExceeded):
        deadline.provider_call(lambda: time.sleep(0.2), 60)
    with pytest.raises(deadline.DeadlineExceeded):
        deadline.provider_call(lambda: pytest.fail("must not start"), 60)


def test_slow_transport_is_bounded_even_if_it_ignores_socket_timeout(budget):
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        deadline.provider_call(lambda: time.sleep(0.3), 0.02)
    assert time.monotonic() - started < 0.1


def test_backoff_cannot_outlive_deadline(budget):
    with pytest.raises(deadline.DeadlineExceeded):
        deadline.pause(60)


def test_cancelled_budget_prevents_transport(budget):
    budget.cancelled.set()
    with pytest.raises(deadline.DeadlineExceeded):
        deadline.provider_call(lambda: pytest.fail("cancelled"), 10)


def test_client_retry_limit_and_remaining_timeout(monkeypatch, budget):
    calls = []
    monkeypatch.setattr(client.settings, "LLM_PROVIDER", "open-router")
    monkeypatch.setattr(client, "MODEL_NAME", "test-model")
    monkeypatch.setattr(client, "pause", lambda seconds: None)
    monkeypatch.setattr(client, "_is_transient_error", lambda exc: True)

    def fail(**kwargs):
        calls.append(kwargs["timeout"])
        raise RuntimeError("temporary failure")

    sdk = SimpleNamespace(responses=SimpleNamespace(create=fail))
    with pytest.raises(RuntimeError):
        client.call_llm("prompt", sdk)
    assert len(calls) == client.MAX_ATTEMPTS_PER_MODEL
    assert all(0 < timeout <= 0.12 for timeout in calls)


def test_fallback_does_not_restart_expired_budget(monkeypatch, budget):
    monkeypatch.setattr(provider_fallback, "_call_openrouter",
                        lambda *a, **kw: (_ for _ in ()).throw(deadline.DeadlineExceeded()))
    with pytest.raises(deadline.DeadlineExceeded):
        provider_fallback._call_provider_with_retry(lambda: object(), "prompt", None, None, "open-router", 4)


def test_api_deadline_returns_controlled_error_and_stops_nested_work(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("BACKEND_API_SECRET", "test-secret")
    monkeypatch.setenv("BACKEND_REQUEST_DEADLINE", "0.04")
    app = FastAPI()
    app.add_middleware(InterviewSecurity)
    finished = Event()
    subsequent = []

    @app.post("/api/interview/slow")
    def slow():
        time.sleep(0.08)
        try:
            deadline.check()
            subsequent.append(True)
        finally:
            finished.set()
        return {"private": "never sent"}

    with TestClient(app) as api:
        response = api.post("/api/interview/slow", headers={"Authorization": "Bearer test-secret"})
        assert response.status_code == 504
        assert "private" not in response.text
        assert finished.wait(1)
    assert not subsequent


def test_openai_sdk_retries_disabled():
    sdk = client.create_openrouter_client("dummy")
    assert sdk.max_retries == 0
    sdk.close()


def test_ollama_slow_provider_stops_before_fallback(monkeypatch, budget):
    from interview_app_backend.llm import ollama_client
    monkeypatch.setattr(client.settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(client.settings, "OLLAMA_API_KEY", "dummy")
    monkeypatch.setattr(client.settings, "OLLAMA_HOST", "https://ollama.com")
    monkeypatch.setattr(client.settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    calls = []

    def slow(**kwargs):
        calls.append(kwargs["timeout"])
        time.sleep(0.25)

    monkeypatch.setattr(ollama_client.requests, "post", lambda *args, **kwargs: slow(**kwargs))
    monkeypatch.setattr(client, "create_openrouter_client", lambda key: pytest.fail("expired fallback"))
    with pytest.raises(deadline.DeadlineExceeded):
        client.call_llm("prompt", ollama_client.OllamaCloudClient())
    assert len(calls) == 1
    assert 0 < calls[0] <= 0.12


def test_configured_ollama_fallback_uses_remaining_budget(monkeypatch, budget):
    from interview_app_backend.llm.ollama_client import OllamaCloudClient
    monkeypatch.setattr(client.settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(client.settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    monkeypatch.setattr(client, "OPENROUTER_API_KEY", "dummy")
    monkeypatch.setattr(client, "MODEL_NAME", "test-model")

    def fail(*args):
        time.sleep(0.02)
        raise RuntimeError("temporary failure")

    monkeypatch.setattr(OllamaCloudClient, "call", fail)
    calls = []

    def success(**kwargs):
        calls.append(kwargs["timeout"])
        return {"output_text": "answer"}

    sdk = SimpleNamespace(responses=SimpleNamespace(create=success))
    monkeypatch.setattr(client, "create_openrouter_client", lambda key: sdk)
    assert client.call_llm("prompt", OllamaCloudClient()) == "answer"
    assert 0 < calls[0] < 0.11


def test_independent_async_contexts_do_not_share_deadlines():
    import asyncio

    async def operation(seconds):
        value = deadline.Deadline(time.monotonic() + seconds)
        token = deadline.current_deadline.set(value)
        try:
            await asyncio.sleep(0)
            assert deadline.current_deadline.get() is value
            return deadline.remaining(60)
        finally:
            deadline.current_deadline.reset(token)

    async def run():
        short, long = await asyncio.gather(operation(0.1), operation(1))
        assert short < long
    asyncio.run(run())
