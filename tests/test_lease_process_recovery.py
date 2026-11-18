"""Kill a real worker; let its isolated Redis lease expire without intervention."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
import secrets
import time
from unittest.mock import patch

import httpx
import pytest

from scripts import verify_managed_redis as helper
from tests.lease_lifecycle_support import KEY, redis
from shared.visitor_identity import issue

pytestmark = pytest.mark.skipif(not os.getenv("TEST_REDIS_PORT"), reason="Local Redis required")


def test_killed_worker_capacity_recovers_by_lease_expiry():
    lease_ms = int(os.getenv("LEASE_EXPIRY_TEST_MS", "500"))
    namespace = "lease-crash-local-" + secrets.token_hex(8)
    environment = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "TEST_REDIS_PORT"}}
    environment.update(APP_ENV="test", BACKEND_API_SECRET="synthetic-auth", BACKEND_VISITOR_SIGNING_KEY=KEY,
                       LEASE_TEST_WORKER="1", TEST_LEASE_MS=str(lease_ms),
                       BACKEND_RATE_BACKEND="redis", UPSTASH_REDIS_REST_URL="https://unused.example",
                       UPSTASH_REDIS_REST_TOKEN="synthetic", BACKEND_RATE_NAMESPACE=namespace,
                       BACKEND_RATE_LIMIT="100", BACKEND_MAX_CONCURRENT="1", BACKEND_REQUEST_DEADLINE="270",
                       BACKEND_VISITOR_RATE_LIMIT="100")
    original = helper.subprocess.Popen

    def launch(args, **kwargs):
        args = ["tests.lease_lifecycle_support:app" if arg == "api.index:app" else arg for arg in args]
        return original(args, **kwargs)

    processes = []
    key = "{" + namespace + "}:v4:leases"
    headers = {"Authorization": "Bearer synthetic-auth", "X-Interview-Visitor": issue(KEY)}

    def send(url, delay):
        try:
            return httpx.post(url + "/api/interview/check", headers=headers, json={"delay": delay},
                              timeout=5, trust_env=False)
        except httpx.RequestError:
            return None  # Killing the worker deliberately breaks this connection.

    try:
        with patch.object(helper.subprocess, "Popen", launch):
            processes = [helper.start_backend(environment) for _ in range(2)]
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(send, processes[0][1], 600)
            for _ in range(100):
                owners = redis("ZRANGE", key, 0, -1, "WITHSCORES")
                if owners:
                    break
                time.sleep(0.01)
            else:
                pytest.fail("Worker did not acquire lease")
            assert len(owners) == 2 and len(owners[0]) == 64
            ttl = redis("PTTL", key)
            assert 0 < ttl <= lease_ms
            assert send(processes[1][1], 0).status_code == 429
            helper.stop_backend(processes[0][0])
            killed_at = time.monotonic()
            assert pending.result(timeout=6) is None
        # No DEL, ZREM, clock changes or shortened expiry; Redis restores capacity.
        expiry = float(owners[1])
        while True:
            now = redis("TIME")
            remaining_ms = expiry - (int(now[0]) * 1000 + int(now[1]) // 1000)
            if remaining_ms <= 0:
                break
            time.sleep(min(1, remaining_ms / 1000 + 0.01))
        assert send(processes[1][1], 0).status_code == 200
        recovered_ms = (time.monotonic() - killed_at) * 1000
        assert recovered_ms <= lease_ms + 3000
        print(json.dumps({"leaseMs": lease_ms, "initialTtlMs": ttl, "recoveryAfterKillMs": round(recovered_ms),
                          "independentProcesses": 2, "manualRedisMutation": False}))
    finally:
        for process, _ in processes:
            if process.poll() is None:
                helper.stop_backend(process)
