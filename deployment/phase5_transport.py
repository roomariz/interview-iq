"""No paid/alternate provider can cross the Phase 5 HTTP boundary."""

from contextvars import ContextVar
from decimal import Decimal
import json
import os
from time import monotonic

import httpx
import requests

from deployment import phase5_budget as budget
from deployment.phase5_redis import allows_redis_request, configured_endpoint, guarded_async_send

CURRENT = ContextVar("phase5_workflow", default=None)
_installed = False


def validate_body(body):
    allowed = {"model", "input", "temperature", "max_output_tokens", "provider", "store", "stream"}
    if (set(body) - allowed or body.get("model") != budget.MODEL or body.get("provider") != budget.ROUTING
            or body.get("max_output_tokens") != 2048 or body.get("store") is not False
            or body.get("stream", False) is not False):
        raise RuntimeError("Phase 5 request is outside the free-only allowlist")
    prompt = body.get("input")
    # Gemma's byte fallback cannot use more text tokens than UTF-8 bytes. Reserve
    # half the input allowance for server chat framing; accept only a single turn.
    if not isinstance(prompt, str) or not prompt or len(prompt.encode("utf-8")) > 8192:
        raise RuntimeError("Phase 5 input allowance exceeded")


def validate_result(payload):
    usage = payload.get("usage", {})
    if (payload.get("model") != budget.MODEL or payload.get("status") != "completed"
            or payload.get("error") or not isinstance(usage, dict)):
        raise RuntimeError("Phase 5 provider result failed validation")
    counts = [usage.get("input_tokens"), usage.get("output_tokens")]
    cost = usage.get("cost")
    if (any(type(n) is not int or n < 0 for n in counts) or counts[0] > 16384
            or counts[1] > 2048 or isinstance(cost, bool) or cost is None
            or not Decimal(str(cost)).is_finite() or Decimal(str(cost)) != 0):
        raise RuntimeError("Phase 5 usage or zero cost could not be verified")
    return {"input_tokens": counts[0], "output_tokens": counts[1], "cost": 0}


def check_price(client):
    request = client.build_request("GET", "https://openrouter.ai/api/v1/models/" + budget.MODEL + "/endpoints")
    response = budget.BASE_SEND(client, request, follow_redirects=False)
    response.raise_for_status()
    data = response.json()["data"]
    endpoints = [e for e in data["endpoints"] if e.get("tag") == "google-ai-studio" and e.get("status") == 0]
    if data["id"] != budget.MODEL or not endpoints:
        raise RuntimeError("Phase 5 free route unavailable")
    for endpoint in endpoints:
        prices = endpoint.get("pricing", {})
        if not {"prompt", "completion"}.issubset(prices):
            raise RuntimeError("Phase 5 pricing incomplete")
        if any(Decimal(str(v)) != 0 for k, v in prices.items() if k != "discount"):
            raise RuntimeError("Phase 5 zero pricing unavailable")


def send(client, request, **kwargs):
    url = str(request.url)
    if allows_redis_request(request):
        return budget.BASE_SEND(client, request, **{**kwargs, "follow_redirects": False})
    if (request.method != "POST" or url != "https://openrouter.ai/api/v1/responses"
            or kwargs.get("stream") or not CURRENT.get()):
        raise RuntimeError("Phase 5 egress denied")
    body = json.loads(request.content)
    validate_body(body)
    group, owner = CURRENT.get()
    attempt, number = budget.reserve(group, owner)
    started = monotonic()
    event = {"event": "result", "case": group, "attempt": number, "model": budget.MODEL}
    try:
        check_price(client)
        event["price_verified"] = True
        response = budget.BASE_SEND(client, request, **{**kwargs, "follow_redirects": False})
        response.read()
        event["status"] = response.status_code
        if response.status_code != 200:
            raise RuntimeError("Phase 5 provider HTTP failure")
        event.update(validate_result(response.json()))
        event["usage_valid"] = True
        return response
    except Exception:
        event["usage_valid"] = False
        # A failure closes the entire run before any service/SDK retry can send.
        budget.action("close")
        raise RuntimeError("Phase 5 stopped; consult private numeric diagnostics") from None
    finally:
        event["latency_ms"] = int((monotonic() - started) * 1000)
        # Closed runs still retain this numeric result through a direct append.
        budget.command("RPUSH", budget.keys()[2], json.dumps(event))
        budget.command("HDEL", budget.keys()[0], "active")


def install():
    global _installed
    if _installed:
        return
    expected = {"VERCEL_ENV": "preview", "APP_ENV": "production", "LLM_PROVIDER": "open-router",
                "IS_FREE_MODE": "true", "MODEL_NAME": budget.MODEL,
                "OLLAMA_FALLBACK_TO_OPENROUTER": "false", "BACKEND_RATE_BACKEND": "redis",
                "BACKEND_RATE_NAMESPACE": "interviewiq-mocked-preview", "BACKEND_RATE_LIMIT": "30",
                "BACKEND_GLOBAL_DAILY_LIMIT": "1000", "BACKEND_VISITOR_RATE_LIMIT": "10",
                "BACKEND_VISITOR_DAILY_LIMIT": "100", "BACKEND_MAX_CONCURRENT": "4",
                "BACKEND_INGRESS_RATE_LIMIT": "300", "LLM_TIMEOUT": "60", "BACKEND_REQUEST_DEADLINE": "150"}
    if any(os.getenv(k) != v for k, v in expected.items()):
        raise RuntimeError("Phase 5 deployment configuration refused")
    if any(os.getenv(k) for k in ("OLLAMA_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY")):
        raise RuntimeError("Phase 5 alternative credentials refused")
    from api.configuration import BackendConfig
    BackendConfig.load()
    configured_endpoint()
    from config import settings
    settings.FALLBACK_CHAIN = [budget.MODEL]
    settings.FREE_EVAL_MODELS = [budget.MODEL]
    settings.QUESTION_GENERATION_FALLBACK_CHAIN = [budget.MODEL]
    settings.FALLBACK_PROVIDERS = []
    from openai.resources.responses import Responses
    original_create = Responses.create

    def create(resource, **kwargs):
        if kwargs.get("model") != budget.MODEL or set(kwargs) - {"model", "input", "temperature", "timeout"}:
            raise RuntimeError("Phase 5 model selection refused")
        return original_create(resource, **kwargs, max_output_tokens=2048, store=False,
                               extra_body={"provider": budget.ROUTING})

    def denied(*args, **kwargs):
        raise RuntimeError("Phase 5 alternative transport denied")

    original_async = httpx.AsyncClient.send

    async def async_send(client, request, **kwargs):
        return await guarded_async_send(original_async, client, request, **kwargs)

    Responses.create = create
    httpx.Client.send = send
    httpx.AsyncClient.send = async_send
    requests.sessions.Session.request = denied
    _installed = True
