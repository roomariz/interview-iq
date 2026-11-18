"""Loopback-only synthetic worker for Redis lease lifecycle tests."""

import asyncio
import os
import socket
import time

from fastapi import FastAPI, HTTPException, Request
import pytest

from api.configuration import BackendConfig
from api.rate_limit import SCRIPT
from api.security import InterviewSecurity
from interview_app_backend.llm.deadline import provider_call

KEY = "synthetic-visitor-signing-key-00000000"


@pytest.fixture
def anonymous(monkeypatch):
    for name, value in {"APP_ENV": "test", "BACKEND_API_SECRET": "test-secret",
                        "BACKEND_VISITOR_SIGNING_KEY": KEY, "BACKEND_RATE_BACKEND": "redis",
                        "UPSTASH_REDIS_REST_URL": "https://synthetic.redis.example",
                        "UPSTASH_REDIS_REST_TOKEN": "synthetic-redis-token"}.items():
        monkeypatch.setenv(name, value)
    return BackendConfig.load()


def redis(*parts):
    def read(stream):
        line = stream.readline()
        kind, data = line[:1], line[1:-2]
        if kind == b"-":
            raise RuntimeError("Local Redis command failed")
        if kind == b":":
            return int(data)
        if kind == b"+":
            return data.decode()
        if kind == b"$":
            size = int(data)
            if size == -1:
                return None
            value = stream.read(size)
            stream.read(2)
            return value.decode()
        if kind == b"*":
            return [read(stream) for _ in range(int(data))]
        raise RuntimeError("Invalid local Redis response")

    encoded = [str(p).encode() for p in parts]
    wire = b"*%d\r\n" % len(parts) + b"".join(b"$%d\r\n" % len(p) + p + b"\r\n" for p in encoded)
    with socket.create_connection(("127.0.0.1", int(os.environ["TEST_REDIS_PORT"])), timeout=3) as connection:
        connection.sendall(wire)
        return read(connection.makefile("rb"))


async def command(config, script, keys, args):
    return await asyncio.to_thread(redis, "EVAL", script, len(keys), *keys, *args)


async def ingress(self, config, secret):
    count, ttl = await command(config, SCRIPT, ["{" + config.namespace + "}:ingress"], [])
    return max(1, (ttl + 999) // 1000) if count > config.ingress_rate else 0


def application():
    app = FastAPI()
    app.state.entered = asyncio.Event()
    app.add_middleware(InterviewSecurity)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/interview/check")
    async def check(request: Request):
        body = await request.json()
        app.state.entered.set()
        if body.get("action") == "exception":
            raise HTTPException(502, "synthetic failure")
        if body.get("action") == "unexpected_exception":
            raise RuntimeError("synthetic backend exception")
        if body.get("action") in {"provider_timeout", "provider_cancel"}:
            try:
                timeout = 0.03 if body["action"] == "provider_timeout" else 5
                await asyncio.to_thread(provider_call, lambda: time.sleep(body["delay"]), timeout)
            except TimeoutError:
                raise HTTPException(504, "synthetic timeout") from None
        else:
            await asyncio.sleep(body.get("delay", 0))
        return {"mocked": True}

    return app


if os.getenv("LEASE_TEST_WORKER") == "1":
    import api.admission
    from api.rate_limit import RateLimiter

    api.admission.command = command
    api.admission.LEASE_MS = int(os.getenv("TEST_LEASE_MS", "330000"))
    RateLimiter.retry_after = ingress

app = application()
