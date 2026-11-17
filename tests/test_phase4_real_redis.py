"""Opt-in real Redis Lua tests, including two independent backend processes."""

import asyncio
from dataclasses import replace
import os
import secrets
import time

import httpx
import pytest

from api.admission import Admission
from api.admission_scripts import ADMIT, RELEASE, RENEW
from scripts.verify_managed_redis import start_backend, stop_backend
from tests.phase4_redis_support import command, redis
from tests.test_phase4_admission import anonymous  # noqa: F401
from tests.test_phase4_identity_logging import KEY
from shared.visitor_identity import issue

pytestmark = pytest.mark.skipif(not os.getenv("PHASE4_REDIS_PORT"), reason="Opt-in local real Redis required")


@pytest.fixture
def real(anonymous, monkeypatch):  # noqa: F811
    monkeypatch.setattr("api.admission.command", command)
    return replace(anonymous, namespace="phase4-" + secrets.token_hex(8), max_concurrent=2,
                   visitor_rate=2, visitor_day=3, rate_limit=3, global_day=4)


def test_real_visitor_global_and_non_debiting_busy(real):
    async def run():
        a, b, blocked = [Admission(real, name) for name in ("a", "b", "c")]
        assert (await a.acquire())[0] == 0
        assert (await b.acquire())[0] == 0
        assert (await blocked.acquire())[0] == 2
        assert redis("GET", blocked.keys[0]) is None
        await command(real, RELEASE, [a.keys[4]], [a.owner])
        a.heartbeat.cancel()
        assert (await blocked.acquire())[0] == 0
        await command(real, RELEASE, [b.keys[4]], [b.owner])
        b.heartbeat.cancel()
        denied = Admission(real, "d")
        assert (await denied.acquire())[0] == 1  # Global minute cap.
        assert redis("GET", denied.keys[0]) is None
        blocked.heartbeat.cancel()
    asyncio.run(run())


@pytest.mark.parametrize("daily", [False, True])
def test_real_separate_visitor_and_daily_global_quotas(real, daily):
    async def run():
        config = replace(real, max_concurrent=100, rate_limit=100, visitor_rate=1 if not daily else 100,
                         visitor_day=1 if daily else 100, global_day=2)
        a = Admission(config, "a")
        assert (await a.acquire())[0] == 0
        a.heartbeat.cancel()
        denied = await Admission(config, "a").acquire()
        assert denied[0] == 1
        assert denied[1] > (60 if daily else 0)
        b = Admission(config, "b")
        assert (await b.acquire())[0] == 0
        b.heartbeat.cancel()
        assert (await Admission(config, "c").acquire())[0] == 1
    asyncio.run(run())


def test_real_expiration_renewal_and_owned_release(real):
    async def run():
        a = Admission(real, "a")
        args = [10, 100, 30, 1000, 1, 100, a.owner]
        assert await command(real, ADMIT, a.keys, args) == [0, 0]
        assert await command(real, RELEASE, [a.keys[4]], ["wrong-owner"]) == 0
        assert await command(real, RENEW, [a.keys[4]], [a.owner, 150]) == 1
        assert await command(real, RENEW, [a.keys[4]], ["wrong-owner", 150]) == 0
        await asyncio.sleep(0.2)
        assert await command(real, RENEW, [a.keys[4]], [a.owner, 150]) == 0
        b = Admission(real, "b")
        assert await command(real, ADMIT, b.keys, [10, 100, 30, 1000, 1, 150, b.owner]) == [0, 0]
        assert await command(real, RELEASE, [a.keys[4]], [a.owner]) == 0
        assert redis("ZCARD", b.keys[4]) == 1
        # Quota reset uses expiry, never deleting unrelated keys.
        for key in a.keys[:4]:
            redis("PEXPIRE", key, 1)
        await asyncio.sleep(0.02)
        assert await command(real, ADMIT, a.keys, [10, 100, 30, 1000, 2, 150, a.owner]) == [0, 0]
    asyncio.run(run())


def test_two_backend_processes_enforce_global_concurrency(real):
    environment = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "PHASE4_REDIS_PORT"}}
    environment.update(APP_ENV="test", BACKEND_API_SECRET="synthetic-auth", BACKEND_VISITOR_SIGNING_KEY=KEY,
                       PHASE4_BACKEND_WORKER="1",
                       BACKEND_RATE_BACKEND="redis", UPSTASH_REDIS_REST_URL="https://unused.example",
                       UPSTASH_REDIS_REST_TOKEN="synthetic", BACKEND_RATE_NAMESPACE=real.namespace,
                       BACKEND_RATE_LIMIT="100", BACKEND_MAX_CONCURRENT="2", BACKEND_REQUEST_DEADLINE="2",
                       BACKEND_VISITOR_RATE_LIMIT="100")
    from scripts import verify_managed_redis as helper
    original = helper.subprocess.Popen

    def launch(args, **kwargs):
        args = ["tests.phase4_redis_support:app" if arg == "api.index:app" else arg for arg in args]
        return original(args, **kwargs)

    processes = []
    try:
        from unittest.mock import patch
        with patch.object(helper.subprocess, "Popen", launch):
            processes = [start_backend(environment) for _ in range(2)]
        headers = {"Authorization": "Bearer synthetic-auth", "X-Interview-Visitor": issue(KEY)}
        def send(index, delay=0.4):
            return httpx.post(processes[index % 2][1] + "/api/interview/check", json={"delay": delay},
                              headers=headers, timeout=5, trust_env=False)
        # Prepare connections before simultaneous dispatch, so slow client setup
        # cannot turn the concurrency assertion into sequential batches.
        async def simultaneous():
            async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
                return await asyncio.gather(*[
                    client.post(processes[index % 2][1] + "/api/interview/check", json={"delay": 1},
                                headers=headers) for index in range(12)
                ])
        responses = asyncio.run(simultaneous())
        assert sorted(r.status_code for r in responses) == [200] * 2 + [429] * 10
        assert all(int(r.headers["Retry-After"]) > 0 for r in responses if r.status_code == 429)
        response = send(0, 3)
        assert response.status_code == 504
        time.sleep(0.2)
        assert send(1, 0).status_code == 200
        invalid = httpx.post(processes[0][1] + "/api/interview/check", json={},
                             headers={"Authorization": "Bearer wrong"}, trust_env=False)
        assert invalid.status_code == 401
    finally:
        for process, _ in processes:
            stop_backend(process)
