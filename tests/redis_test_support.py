"""Opt-in local Redis wire adapter and synthetic ASGI app; never invokes an LLM."""

import asyncio
import os
import socket

from fastapi import FastAPI, Request

from api.security import InterviewSecurity
from api.rate_limit import SCRIPT


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
    # Only this test-only entrypoint replaces REST transport with the real Redis wire adapter.
    import api.admission
    from api.rate_limit import RateLimiter
    api.admission.command = command
    RateLimiter.retry_after = ingress
    app = FastAPI()
    app.add_middleware(InterviewSecurity)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/interview/check")
    async def check(request: Request):
        body = await request.json()
        await asyncio.sleep(body.get("delay", 0))
        return {"mocked": True}

    return app


app = application() if os.getenv("REDIS_TEST_WORKER") == "1" else FastAPI()
