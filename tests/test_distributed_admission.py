"""Mocked HTTP admission failures and work-lease lifetime."""

import asyncio
from dataclasses import replace
from threading import Event
from time import monotonic

import httpx
import pytest

from api.admission import Admission
from api.configuration import BackendConfig
from api.admission_scripts import ADMIT, RELEASE
from interview_app_backend.llm.deadline import Deadline, current_deadline, provider_call
from shared.visitor_identity import issue
from tests.test_shared_rate_limits import application
from tests.test_anonymous_identity_logging import KEY


@pytest.fixture
def anonymous(monkeypatch):
    for name, value in {"APP_ENV": "test", "BACKEND_API_SECRET": "test-secret",
                        "BACKEND_VISITOR_SIGNING_KEY": KEY, "BACKEND_RATE_BACKEND": "redis",
                        "UPSTASH_REDIS_REST_URL": "https://synthetic.redis.example",
                        "UPSTASH_REDIS_REST_TOKEN": "synthetic-redis-token"}.items():
        monkeypatch.setenv(name, value)
    return BackendConfig.load()


@pytest.mark.parametrize("auth,visitor,status", [("wrong", issue(KEY), 401),
                                                ("test-secret", "arbitrary", 401),
                                                ("test-secret", "", 401)])
def test_auth_and_identity_rejected_before_redis(anonymous, monkeypatch, auth, visitor, status):
    async def forbidden(*args, **kwargs):
        pytest.fail("Redis must not be called")
    monkeypatch.setattr("api.admission.command", forbidden)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application()), base_url="http://test") as c:
            r = await c.post("/api/interview/check", headers={"Authorization": f"Bearer {auth}",
                                                           "X-Interview-Visitor": visitor})
            assert r.status_code == status
    asyncio.run(run())


@pytest.mark.parametrize("response", [[True, 0], [0, 1], [7, 0], [1, -1], [1, 86400001], {}, None])
def test_invalid_admission_fails_closed(anonymous, monkeypatch, response):
    async def command(*args):
        return response
    monkeypatch.setattr("api.admission.command", command)
    with pytest.raises(ValueError):
        asyncio.run(Admission(anonymous, "opaque").acquire())


def test_outage_no_memory_fallback(anonymous, monkeypatch):
    async def command(*args):
        raise httpx.ConnectError("sensitive infrastructure")
    monkeypatch.setattr("api.admission.command", command)
    with pytest.raises(httpx.ConnectError):
        asyncio.run(Admission(anonymous, "opaque").acquire())


def test_lease_retained_until_abandoned_transport_finishes(anonymous, monkeypatch):
    entered, finish = Event(), Event()
    calls = []
    async def command(config, script, keys, args):
        calls.append(script)
        return [0, 0] if script == ADMIT else 1
    monkeypatch.setattr("api.admission.command", command)

    def operation():
        entered.set()
        finish.wait(5)

    async def run():
        admission = Admission(anonymous, "opaque")
        await admission.acquire()
        deadline = Deadline(monotonic() + 1)
        token = current_deadline.set(deadline)
        try:
            with pytest.raises(TimeoutError):
                provider_call(operation, 0.01)
            assert entered.is_set()
            deadline.cancelled.set()
            await admission.finish(deadline)
            await asyncio.sleep(0.02)
            assert RELEASE not in calls
            finish.set()
            for _ in range(30):
                if RELEASE in calls:
                    break
                await asyncio.sleep(0.02)
            assert RELEASE in calls
        finally:
            finish.set()
            current_deadline.reset(token)
    asyncio.run(run())


def test_separate_key_and_limits_required(anonymous, monkeypatch):
    monkeypatch.setenv("BACKEND_VISITOR_SIGNING_KEY", "test-secret")
    with pytest.raises(ValueError):
        BackendConfig.load()
    assert replace(anonymous, visitor_key="").environment == "test"


@pytest.mark.parametrize("failure", ["http", "outage", "malformed"])
def test_middleware_admission_outage_is_sanitised(anonymous, monkeypatch, failure):
    original = httpx.AsyncClient

    async def ingress(*args):
        return 0

    def respond(request):
        if failure == "outage":
            raise httpx.ConnectError("private endpoint credentials")
        return httpx.Response(500 if failure == "http" else 200, json={"error": "private endpoint credentials"})

    monkeypatch.setattr("api.rate_limit.RateLimiter.retry_after", ingress)
    monkeypatch.setattr("api.admission.httpx.AsyncClient", lambda **kw: original(
        transport=httpx.MockTransport(respond), **kw))

    async def run():
        async with original(transport=httpx.ASGITransport(app=application()), base_url="http://test") as client:
            response = await client.post("/api/interview/check", headers={
                "Authorization": "Bearer test-secret", "X-Interview-Visitor": issue(KEY)})
            assert response.status_code == 503
            assert response.headers["Retry-After"] == "5"
            assert "private" not in response.text
    asyncio.run(run())


def test_invalid_payload_does_not_take_work_allowance(anonymous, monkeypatch):
    async def ingress(*args):
        return 0

    async def forbidden(*args):
        pytest.fail("Invalid input must not be admitted")

    monkeypatch.setattr("api.rate_limit.RateLimiter.retry_after", ingress)
    monkeypatch.setattr("api.admission.command", forbidden)

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application()), base_url="http://test") as client:
            response = await client.post("/api/interview/context", content=b"invalid-json", headers={
                "Authorization": "Bearer test-secret", "X-Interview-Visitor": issue(KEY)})
            assert response.status_code == 422
    asyncio.run(run())


@pytest.mark.parametrize("result", [0, True, "outage"])
def test_lease_renewal_failure_cancels_new_provider_work(anonymous, monkeypatch, result):
    async def no_wait(seconds):
        pass

    async def command(*args):
        if result == "outage":
            raise httpx.ConnectError("private endpoint")
        return result

    monkeypatch.setattr("api.admission.asyncio.sleep", no_wait)
    monkeypatch.setattr("api.admission.command", command)

    async def run():
        deadline = Deadline(monotonic() + 10)
        token = current_deadline.set(deadline)
        try:
            admission = Admission(anonymous, "opaque")
            await admission.renew()
            assert deadline.cancelled.is_set()
        finally:
            current_deadline.reset(token)
    asyncio.run(run())
