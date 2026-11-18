"""Real Redis: expiration, cancellation and recovery without deleting shared keys."""

import asyncio
from dataclasses import replace
import os
import secrets
import time

import httpx
import pytest

from api.admission import Admission, LEASE_MS
from api.admission_scripts import ADMIT, RENEW
from interview_app_backend.llm.deadline import Deadline
from tests.lease_lifecycle_support import KEY, application, command, ingress, redis
from tests.lease_lifecycle_support import anonymous  # noqa: F401
from shared.visitor_identity import issue

pytestmark = pytest.mark.skipif(not os.getenv("TEST_REDIS_PORT"), reason="Local Redis required")


@pytest.fixture
def isolated(anonymous, monkeypatch):  # noqa: F811
    namespace = "lease-local-" + secrets.token_hex(8)
    monkeypatch.setenv("BACKEND_RATE_NAMESPACE", namespace)
    monkeypatch.setenv("BACKEND_MAX_CONCURRENT", "1")
    monkeypatch.setenv("BACKEND_VISITOR_RATE_LIMIT", "100")
    monkeypatch.setattr("api.admission.command", command)
    monkeypatch.setattr("api.rate_limit.RateLimiter.retry_after", ingress)
    return replace(anonymous, namespace=namespace, max_concurrent=1, visitor_rate=100)


def headers():
    return {"Authorization": "Bearer test-secret", "X-Interview-Visitor": issue(KEY)}


async def wait_for_count(config, expected):
    key = "{" + config.namespace + "}:v4:leases"
    for _ in range(100):
        if redis("ZCARD", key) == expected:
            return
        await asyncio.sleep(0.01)
    pytest.fail("Lease count did not settle")


@pytest.mark.parametrize("action,status", [("success", 200), ("exception", 502),
                                          ("unexpected_exception", 500), ("provider_timeout", 504),
                                          ("aggregate_timeout", 504)])
def test_completion_exception_and_transport_timeout(isolated, monkeypatch, action, status):
    if action == "aggregate_timeout":
        monkeypatch.setenv("BACKEND_REQUEST_DEADLINE", "0.15")
    async def run():
        transport = httpx.ASGITransport(app=application(), raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.post("/api/interview/check", headers=headers(),
                                    json={"action": action, "delay": 0.25 if status == 504 else 0})
            assert response.status_code == status
            if action == "provider_timeout":
                # Capacity must remain held while the abandoned synchronous transport runs.
                await wait_for_count(isolated, 1)
                denied = await c.post("/api/interview/check", headers=headers(), json={})
                assert denied.status_code == 429
            await wait_for_count(isolated, 0)
            assert (await c.post("/api/interview/check", headers=headers(), json={})).status_code == 200
    asyncio.run(run())


@pytest.mark.parametrize("action", ["success", "provider_cancel"])
def test_request_cancellation_restores_capacity(isolated, action):
    async def run():
        app = application()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            pending = asyncio.create_task(c.post("/api/interview/check", headers=headers(),
                                                 json={"action": action, "delay": 0.4}))
            await wait_for_count(isolated, 1)
            await asyncio.wait_for(app.state.entered.wait(), 1)
            await asyncio.sleep(0.02)
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            if action == "provider_cancel":
                await wait_for_count(isolated, 1)
            await wait_for_count(isolated, 0)
            assert (await c.post("/api/interview/check", headers=headers(), json={})).status_code == 200
    asyncio.run(run())


def test_cancellation_after_redis_commit_before_reply_expires_safely(isolated, monkeypatch):
    monkeypatch.setattr("api.admission.LEASE_MS", 100)

    async def run():
        committed = asyncio.Event()

        async def delayed_reply(config, script, keys, args):
            result = await command(config, script, keys, args)
            if script == ADMIT:
                committed.set()
                await asyncio.sleep(10)
            return result

        monkeypatch.setattr("api.admission.command", delayed_reply)
        a = Admission(isolated, "cancelled-acquisition")
        pending = asyncio.create_task(a.acquire())
        await asyncio.wait_for(committed.wait(), 1)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert a.heartbeat is None and redis("ZSCORE", a.keys[4], a.owner) is not None
        await asyncio.sleep(0.15)
        monkeypatch.setattr("api.admission.command", command)
        b = Admission(isolated, "recovered")
        assert (await b.acquire())[0] == 0
        await b.finish(Deadline(time.monotonic() + 1))
    asyncio.run(run())


def test_expired_member_is_not_occupied_capacity(isolated):
    async def run():
        a, b, c = [Admission(isolated, visitor) for visitor in ("a", "b", "c")]
        assert await command(isolated, ADMIT, a.keys, [100, 100, 100, 1000, 2, 80, a.owner]) == [0, 0]
        assert await command(isolated, ADMIT, b.keys, [100, 100, 100, 1000, 2, 1000, b.owner]) == [0, 0]
        await asyncio.sleep(0.12)
        now = redis("TIME")
        now_ms = int(now[0]) * 1000 + int(now[1]) // 1000
        assert redis("ZCARD", a.keys[4]) == 2
        assert redis("ZCOUNT", a.keys[4], "(" + str(now_ms), "+inf") == 1
        assert await command(isolated, RENEW, [a.keys[4]], [a.owner, 1000]) == 0
        assert await command(isolated, ADMIT, c.keys, [100, 100, 100, 1000, 2, 1000, c.owner]) == [0, 0]
        assert redis("ZSCORE", a.keys[4], a.owner) is None
        assert redis("ZCARD", a.keys[4]) == 2
    asyncio.run(run())


def test_heartbeat_renews_owned_expiry_and_finish_releases(isolated, monkeypatch):
    sleep = asyncio.sleep

    async def accelerated(seconds):
        await sleep(0.03 if seconds == 30 else seconds)

    monkeypatch.setattr("api.admission.asyncio.sleep", accelerated)
    async def run():
        a = Admission(isolated, "a")
        assert (await a.acquire())[0] == 0
        assert len(a.owner) == 64 and LEASE_MS == 330000
        initial = float(redis("ZSCORE", a.keys[4], a.owner))
        assert 329000 <= redis("PTTL", a.keys[4]) <= LEASE_MS
        for _ in range(100):
            if float(redis("ZSCORE", a.keys[4], a.owner)) > initial:
                break
            await sleep(0.01)
        else:
            pytest.fail("Owned heartbeat did not extend expiry")
        assert await command(isolated, RENEW, [a.keys[4]], ["wrong-owner", LEASE_MS]) == 0
        await a.finish(Deadline(time.monotonic() + 1))
        assert redis("ZCARD", a.keys[4]) == 0
    asyncio.run(run())
