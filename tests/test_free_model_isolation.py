"""SDK wire controls, provider isolation and the authenticated workflow boundary."""

import asyncio
import json
import secrets

import httpx
from openai import OpenAI
from openai.resources.responses import Responses
import pytest
import requests

from deployment import free_model_budget as budget
from deployment import free_model_transport as transport
from deployment.live_verification_gate import LiveVerificationGate
from tests.test_free_model_budget import ledger, result  # noqa: F401
from shared.visitor_identity import issue


@pytest.fixture
def installed(monkeypatch, ledger):  # noqa: F811
    settings = {"VERCEL_ENV": "preview", "APP_ENV": "production", "LLM_PROVIDER": "open-router",
                "IS_FREE_MODE": "true", "MODEL_NAME": budget.MODEL, "OPENROUTER_API_KEY": "synthetic",
                "OLLAMA_FALLBACK_TO_OPENROUTER": "false", "BACKEND_RATE_BACKEND": "redis",
                "BACKEND_RATE_NAMESPACE": "interviewiq-mocked-preview",
                "UPSTASH_REDIS_REST_URL": "https://synthetic.redis.invalid", "UPSTASH_REDIS_REST_TOKEN": "synthetic",
                "BACKEND_API_SECRET": "synthetic-backend-" + secrets.token_hex(24),
                "BACKEND_VISITOR_SIGNING_KEY": "synthetic-visitor-" + secrets.token_hex(24),
                "BACKEND_RATE_LIMIT": "30", "BACKEND_GLOBAL_DAILY_LIMIT": "1000",
                "BACKEND_VISITOR_RATE_LIMIT": "10", "BACKEND_VISITOR_DAILY_LIMIT": "100",
                "BACKEND_MAX_CONCURRENT": "4", "BACKEND_INGRESS_RATE_LIMIT": "300",
                "LLM_TIMEOUT": "60", "BACKEND_REQUEST_DEADLINE": "150"}
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    for name in ("OLLAMA_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    from config import settings as config
    for name in ("FALLBACK_CHAIN", "FREE_EVAL_MODELS", "QUESTION_GENERATION_FALLBACK_CHAIN", "FALLBACK_PROVIDERS"):
        monkeypatch.setattr(config, name, getattr(config, name))
    monkeypatch.setattr(transport, "_installed", False)
    monkeypatch.setattr(Responses, "create", Responses.create)
    monkeypatch.setattr(httpx.Client, "send", httpx.Client.send)
    monkeypatch.setattr(httpx.AsyncClient, "send", httpx.AsyncClient.send)
    monkeypatch.setattr(requests.sessions.Session, "request", requests.sessions.Session.request)
    transport.install()
    return ledger


def test_sdk_wire_model_price_and_token_controls(installed):
    owner = budget.workflow("question")
    token = transport.CURRENT.set(("question", owner))
    seen = []

    def handler(request):
        seen.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"id": budget.MODEL, "endpoints": [{
                "tag": "google-ai-studio", "status": 0, "pricing": {"prompt": "0", "completion": "0"}}]}})
        payload = result()
        payload.update(id="synthetic-response", created_at=1, object="response", output=[])
        return httpx.Response(200, json=payload)

    try:
        with OpenAI(api_key="synthetic", base_url="https://openrouter.ai/api/v1", max_retries=0,
                    http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
            client.responses.create(model=budget.MODEL, input="Synthetic interview question")
            with pytest.raises(RuntimeError):
                client.responses.create(model="openai/gpt-5-nano", input="Synthetic")
        posts = [r for r in seen if r.method == "POST"]
        assert len(posts) == 1
        body = json.loads(posts[0].content)
        assert body["provider"] == budget.ROUTING and body["max_output_tokens"] == 2048
        assert body["store"] is False
    finally:
        transport.CURRENT.reset(token)


@pytest.mark.parametrize("url", ["https://ollama.com/api/chat", "https://api.x.ai/v1/responses",
                                  "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                                  "https://openrouter.ai/api/v1/chat/completions", "https://example.com"])
def test_alternate_sync_egress_refused(installed, url):
    with httpx.Client() as client, pytest.raises(RuntimeError, match="egress denied"):
        client.post(url, json={})


def test_requests_and_async_provider_egress_refused(installed):
    with pytest.raises(RuntimeError):
        requests.post("https://ollama.com/api/chat")

    async def run():
        async with httpx.AsyncClient() as client:
            with pytest.raises(RuntimeError):
                await client.post("https://openrouter.ai/api/v1/responses", json={})
    asyncio.run(run())


@pytest.mark.parametrize("prices", [{"prompt": "0.0001", "completion": "0"}, {"prompt": "0"}])
def test_changed_or_missing_price_refused(prices, monkeypatch):
    payload = {"data": {"id": budget.MODEL, "endpoints": [{"tag": "google-ai-studio", "status": 0,
                                                           "pricing": prices}]}}
    monkeypatch.setattr(budget, "BASE_SEND", lambda *a, **k: httpx.Response(200, json=payload,
                        request=httpx.Request("GET", "https://synthetic.invalid")))
    with httpx.Client() as client, pytest.raises(RuntimeError):
        transport.check_price(client)


def test_gate_denies_replays_and_does_not_spend_on_invalid_input(ledger, monkeypatch):  # noqa: F811
    key = "synthetic-signing-key-" + secrets.token_hex(16)
    monkeypatch.setenv("BACKEND_API_SECRET", "synthetic-backend-secret")
    monkeypatch.setenv("BACKEND_VISITOR_SIGNING_KEY", key)
    called = []

    async def app(scope, receive, send):
        called.append(True)
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        payload = {"llm_metadata": {"model": budget.MODEL, "status": "success"}}
        await send({"type": "http.response.body", "body": json.dumps(payload).encode()})

    async def call(body, authorised=True):
        headers = [(b"authorization", b"Bearer synthetic-backend-secret"),
                   (b"x-interview-visitor", issue(key).encode()), (b"x-live-verification-case", b"question")]
        scope = {"type": "http", "method": "POST", "path": "/api/interview/question",
                 "headers": headers if authorised else []}
        messages = []

        async def receive():
            return {"type": "http.request", "body": json.dumps(body).encode(), "more_body": False}

        async def send(message):
            messages.append(message)
        await LiveVerificationGate(app)(scope, receive, send)
        return messages[0]["status"]

    assert asyncio.run(call({"role": "Engineer", "question_list_count": 1}, False)) == 401
    assert asyncio.run(call({"role": "Engineer", "question_list_count": 5})) == 422
    assert not called
    assert asyncio.run(call({"role": "Engineer", "question_list_count": 1})) == 200
    assert asyncio.run(call({"role": "Engineer", "question_list_count": 1})) == 503
    assert len(called) == 1
