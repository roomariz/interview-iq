"""Free-only request enforcement and real local Redis budget race checks."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
import secrets

import httpx
import pytest

from deployment import free_model_budget as budget
from deployment import free_model_transport as transport
from tests.redis_test_support import redis


def body():
    return {"model": budget.MODEL, "input": "Synthetic interview prompt", "store": False,
            "provider": deepcopy(budget.ROUTING), "max_output_tokens": 2048}


@pytest.mark.parametrize("change", [
    {"model": "openai/gpt-5-nano"}, {"model": "google/gemma-3-12b-it:free"},
    {"provider": {"max_price": {"prompt": 1, "completion": 1}}},
    {"tools": [{"type": "web_search"}]}, {"stream": True}, {"store": True},
    {"max_output_tokens": 2049}, {"models": [budget.MODEL]}, {"input": "a" * 8193},
])
def test_disallowed_request(change):
    with pytest.raises(RuntimeError):
        transport.validate_body({**body(), **change})


def test_exact_free_body_and_byte_bound():
    transport.validate_body(body())
    transport.validate_body({**body(), "input": "a" * 8192})
    with pytest.raises(RuntimeError):
        transport.validate_body({**body(), "input": "é" * 4097})


def result():
    return {"model": budget.MODEL, "status": "completed",
            "usage": {"input_tokens": 100, "output_tokens": 20, "cost": 0}}


@pytest.mark.parametrize("cost", [None, 0.001, -1, True, "NaN", "Infinity"])
def test_missing_or_paid_usage_refused(cost):
    payload = result()
    payload["usage"]["cost"] = cost
    with pytest.raises(RuntimeError):
        transport.validate_result(payload)


@pytest.mark.parametrize("change", [{"status": "incomplete"}, {"model": "other"}, {"error": {"code": 1}}])
def test_wrong_or_incomplete_result(change):
    with pytest.raises(RuntimeError):
        transport.validate_result({**result(), **change})


def test_free_usage():
    assert transport.validate_result(result()) == {"input_tokens": 100, "output_tokens": 20, "cost": 0}


@pytest.fixture
def ledger(monkeypatch):
    port = os.getenv("LIVE_VERIFICATION_REDIS_PORT")
    if not port:
        pytest.skip("Opt-in disposable Redis required: LIVE_VERIFICATION_REDIS_PORT")
    monkeypatch.setenv("TEST_REDIS_PORT", port)
    monkeypatch.setenv("LIVE_VERIFICATION_RUN_ID", secrets.token_hex(16))
    monkeypatch.setattr(budget, "command", redis)
    root, _, _ = budget.keys()
    seconds = int(redis("TIME")[0])
    redis("HSET", root, "open", 1, "phase", "question", "expires_ms", seconds * 1000 + 1800000)
    redis("EXPIRE", root, 86400)
    return root


def test_retry_budget_and_three_workflows(ledger):
    total = 0
    for group, maximum in budget.CASE_LIMITS.items():
        redis("HSET", ledger, "phase", group)
        owner = budget.workflow(group)
        with pytest.raises(RuntimeError):
            budget.workflow(group)
        for _ in range(maximum):
            _, number = budget.reserve(group, owner)
            total += 1
            assert number == total
            redis("HDEL", ledger, "active")
            redis("DEL", budget.keys()[1])  # Disposable test namespace only.
        with pytest.raises(RuntimeError):
            budget.reserve(group, owner)
    assert int(redis("HGET", ledger, "attempts")) == 12
    assert int(redis("HGET", ledger, "workflows")) == 3
    assert int(redis("HGET", ledger, "reserved_input")) == 196608
    assert int(redis("HGET", ledger, "reserved_output")) == 24576


def test_simultaneous_workers_cannot_exceed_last_attempt(ledger):
    owner = budget.workflow("question")
    redis("HSET", ledger, "attempts", 11)

    def attempt(_):
        try:
            return budget.reserve("question", owner)[1]
        except RuntimeError:
            return 0

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(attempt, range(32)))
    assert results.count(12) == 1 and results.count(0) == 31
    assert redis("HGET", ledger, "attempts") == "12"


@pytest.mark.parametrize("field,value", [("open", 0), ("expires_ms", 0), ("phase", "evaluation")])
def test_closed_expired_or_wrong_phase(ledger, field, value):
    redis("HSET", ledger, field, value)
    with pytest.raises(RuntimeError):
        budget.workflow("question")


def test_rate_and_owner_controls(ledger):
    owner = budget.workflow("question")
    with pytest.raises(RuntimeError):
        budget.reserve("question", "wrong-owner")
    now = redis("TIME")
    stamp = int(now[0]) * 1000 + int(now[1]) // 1000
    for n in range(10):
        redis("ZADD", budget.keys()[1], stamp, str(n))
    with pytest.raises(RuntimeError):
        budget.reserve("question", owner)
    assert redis("HGET", ledger, "attempts") is None


@pytest.mark.parametrize("status,payload", [(401, {}), (402, {}), (429, {}), (500, {}),
                                           (200, {"invalid": True}), (200, result())])
def test_numeric_telemetry_and_failure_close(monkeypatch, status, payload):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.invalid")
    monkeypatch.setenv("LIVE_VERIFICATION_RUN_ID", "syntheticrunidentity")
    calls = []
    monkeypatch.setattr(budget, "reserve", lambda *a: ("attempt", 1))
    monkeypatch.setattr(budget, "action", lambda *a: calls.append(a))
    monkeypatch.setattr(budget, "command", lambda *a: calls.append(a))
    monkeypatch.setattr(transport, "check_price", lambda c: None)
    monkeypatch.setattr(budget, "BASE_SEND", lambda *a, **k: httpx.Response(status, json=payload))
    token = transport.CURRENT.set(("question", "owner"))
    try:
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/responses", json=body())
        if payload == result():
            assert transport.send(None, request).status_code == 200
            assert ("close",) not in calls
        else:
            with pytest.raises(RuntimeError):
                transport.send(None, request)
            assert ("close",) in calls
        event = next(json.loads(c[2]) for c in calls if c[0] == "RPUSH")
        assert "latency_ms" in event and "input" not in event
    finally:
        transport.CURRENT.reset(token)
