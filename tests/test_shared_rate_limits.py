"""Independent application instances share authenticated quotas."""

import asyncio
from dataclasses import replace

import httpx
import pytest
from fastapi import FastAPI

from api.configuration import BackendConfig
from api.rate_limit import RateLimiter, SCRIPT
from api.security import InterviewSecurity


@pytest.fixture
def config(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("BACKEND_API_SECRET", "test-secret")
    monkeypatch.setenv("BACKEND_RATE_BACKEND", "redis")
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.example")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "redis-secret")
    monkeypatch.setenv("BACKEND_RATE_LIMIT", "2")
    return BackendConfig.load()


def application():
    app = FastAPI()
    app.add_middleware(InterviewSecurity)

    @app.post("/api/interview/check")
    def check():
        return {"ok": True}

    return app


def test_independent_instances_share_atomic_quota(config, monkeypatch):
    counts = {}
    original = httpx.AsyncClient

    async def redis(request):
        import json
        command = json.loads(request.content)
        assert command[:3] == ["EVAL", SCRIPT, "1"]
        assert request.headers["Authorization"] == "Bearer redis-secret"
        key = command[3]
        assert "test-secret" not in key
        counts[key] = counts.get(key, 0) + 1
        return httpx.Response(200, json={"result": [counts[key], 59001]})

    def shared_client(**kwargs):
        return original(transport=httpx.MockTransport(redis), **kwargs)

    monkeypatch.setattr("api.rate_limit.httpx.AsyncClient", shared_client)

    async def run():
        apps = [application(), application()]
        async with original(transport=httpx.ASGITransport(app=apps[0]), base_url="http://test") as first, original(
            transport=httpx.ASGITransport(app=apps[1]), base_url="http://test"
        ) as second:
            invalid = await first.post("/api/interview/check", headers={"X-Forwarded-For": "arbitrary"})
            assert invalid.status_code == 401
            assert not counts
            headers = {"Authorization": "Bearer test-secret", "X-User-ID": "spoofed"}
            responses = await asyncio.gather(*[
                api.post("/api/interview/check", headers=headers) for api in [first, second, first, second]
            ])
            assert sorted(r.status_code for r in responses) == [200, 200, 429, 429]
            assert all(r.headers["Retry-After"] == "60" for r in responses if r.status_code == 429)
        assert len(counts) == 1

    asyncio.run(run())


@pytest.mark.parametrize("payload", [{"error": "private redis details"}, {"result": [True, 30]},
                                      {"result": [1, -1]}, {"result": [1, 60001]}])
def test_shared_service_invalid_response_fails_closed(config, monkeypatch, payload):
    original = httpx.AsyncClient
    monkeypatch.setattr("api.rate_limit.httpx.AsyncClient", lambda **kwargs: original(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)), **kwargs))

    async def run():
        async with original(transport=httpx.ASGITransport(app=application()), base_url="http://test") as api:
            response = await api.post("/api/interview/check", headers={"Authorization": "Bearer test-secret"})
            assert response.status_code == 503
            assert "private redis" not in response.text
    asyncio.run(run())


def test_shared_service_outage_never_uses_local_quota(config, monkeypatch):
    original = httpx.AsyncClient

    def fail(request):
        raise httpx.ConnectError("private host details")

    monkeypatch.setattr("api.rate_limit.httpx.AsyncClient", lambda **kwargs: original(
        transport=httpx.MockTransport(fail), **kwargs))
    with pytest.raises(httpx.ConnectError):
        asyncio.run(RateLimiter().retry_after(config, "secret"))


def test_local_option(config):
    limiter = RateLimiter()
    local = replace(config, rate_backend="memory")
    assert asyncio.run(limiter.retry_after(local, "secret")) == 0
    assert asyncio.run(limiter.retry_after(local, "secret")) == 0
    assert asyncio.run(limiter.retry_after(local, "secret")) > 0


@pytest.mark.parametrize("name,value", [("BACKEND_RATE_BACKEND", "memory"), ("BACKEND_REQUEST_DEADLINE", "nan"),
                                       ("BACKEND_API_SECRET", "short"), ("UPSTASH_REDIS_REST_TOKEN", ""),
                                       ("UPSTASH_REDIS_REST_URL", "http://redis.example"),
                                       ("BACKEND_RATE_NAMESPACE", "bad:namespace")])
def test_production_rejects_unsafe_configuration(config, monkeypatch, name, value):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BACKEND_API_SECRET", "x" * 40)
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        BackendConfig.load()


def test_vercel_cannot_select_local_controls(config, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("APP_ENV", "local")
    with pytest.raises(ValueError):
        BackendConfig.load()


@pytest.mark.parametrize("environment", ["test", "production"])
def test_nonlocal_provider_settings_never_read_dotenv(monkeypatch, environment):
    import runpy
    from unittest.mock import patch
    monkeypatch.setenv("APP_ENV", environment)
    monkeypatch.setenv("OPENROUTER_API_KEY", "environment-key")
    with patch("dotenv.load_dotenv") as load, patch("dotenv.dotenv_values") as values:
        result = runpy.run_path("config/settings.py")
    load.assert_not_called()
    values.assert_not_called()
    assert result["OPENROUTER_API_KEY"] == "environment-key"


def test_vercel_dependency_manifest_matches_backend_requirements():
    import tomllib
    from pathlib import Path
    manifest = tomllib.loads(Path("pyproject.toml").read_text())
    assert set(manifest["project"]["dependencies"]) == set(Path("requirements-backend.txt").read_text().splitlines())
    assert manifest["tool"]["vercel"]["entrypoint"] == "api.index:app"
