"""Admission failure paths preserve authentication and shared quota semantics."""

import asyncio

import httpx
import pytest

from tests.test_phase3_rate_limit import application, config  # noqa: F401


@pytest.mark.usefixtures("config")
@pytest.mark.parametrize("status", [401, 403, 500])
def test_redis_http_failure_is_sanitised_and_fails_closed(monkeypatch, status):
    original = httpx.AsyncClient
    monkeypatch.setattr("api.rate_limit.httpx.AsyncClient", lambda **kwargs: original(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, text="private redis details")),
        **kwargs,
    ))

    async def run():
        async with original(transport=httpx.ASGITransport(app=application()), base_url="http://test") as client:
            response = await client.post("/api/interview/check", headers={"Authorization": "Bearer test-secret"})
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "5"
        assert response.json() == {"error": {
            "code": "rate_service", "message": "Interview service is temporarily unavailable.",
        }}
        assert "private redis" not in response.text
    asyncio.run(run())
