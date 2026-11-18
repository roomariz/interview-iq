"""The Redis guard accepts equivalent roots, never a different destination."""

import asyncio

import httpx
import pytest

from deployment import phase5_budget as budget
from deployment import phase5_transport as transport


@pytest.mark.parametrize("configured", ["https://redis.example.test", "https://redis.example.test/"])
@pytest.mark.parametrize("destination", ["https://redis.example.test", "https://redis.example.test/",
                                         "https://REDIS.example.test:443/"])
def test_equivalent_sync_redis_roots(monkeypatch, configured, destination):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", configured)
    seen = []

    def original(client, request, **kwargs):
        seen.append((request, kwargs))
        return httpx.Response(200, json={"result": "PONG"}, request=request)

    monkeypatch.setattr(budget, "BASE_SEND", original)
    request = httpx.Request("POST", destination, json=["PING"], headers={"Authorization": "Bearer synthetic"})
    response = transport.send(None, request, follow_redirects=True)
    assert response.json() == {"result": "PONG"}
    assert seen[0][0].headers["Authorization"] == "Bearer synthetic"
    assert seen[0][1]["follow_redirects"] is False


@pytest.mark.parametrize("destination", [
    "http://redis.example.test/", "https://other.example.test/", "https://redis.example.test:8443/",
    "https://redis.example.test/commands", "https://redis.example.test//", "https://redis.example.test/%2f",
    "https://redis.example.test/?key=value", "https://redis.example.test/#fragment",
    "https://user:password@redis.example.test/", "https://redis.example.test.evil.test/",
    "https://redis.example.test./",
])
def test_mismatched_sync_redis_endpoint_never_sends(monkeypatch, destination):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.example.test/")
    monkeypatch.setattr(budget, "BASE_SEND", lambda *a, **k: pytest.fail("Unauthorised egress"))
    with pytest.raises(RuntimeError, match="egress denied"):
        transport.send(None, httpx.Request("POST", destination, json=["PING"]))


@pytest.mark.parametrize("configured", ["http://redis.example.test", "https://redis.example.test/path",
                                        "https://user@redis.example.test", "https://redis.example.test/?",
                                        "https://redis.example.test/#", "https://redis.example.test:",
                                        "https://redis.example.test:65536", "https://redis.example.test/\n"])
def test_invalid_configuration_fails_closed(monkeypatch, configured):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", configured)
    monkeypatch.setattr(budget, "BASE_SEND", lambda *a, **k: pytest.fail("Unauthorised egress"))
    with pytest.raises(RuntimeError):
        transport.send(None, httpx.Request("POST", "https://redis.example.test/", json=["PING"]))


def test_get_cannot_use_redis_allowlist(monkeypatch):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.example.test")
    monkeypatch.setattr(budget, "BASE_SEND", lambda *a, **k: pytest.fail("Unauthorised egress"))
    with pytest.raises(RuntimeError):
        transport.send(None, httpx.Request("GET", "https://redis.example.test/"))


@pytest.mark.parametrize("destination", ["https://redis.example.test", "https://redis.example.test/",
                                         "https://other.example.test/", "http://redis.example.test/",
                                         "https://redis.example.test:8443/", "https://redis.example.test/path"])
def test_async_guard_uses_the_same_endpoint_policy(monkeypatch, destination):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.example.test/")
    from deployment.phase5_redis import guarded_async_send
    request = httpx.Request("POST", destination, headers={"Authorization": "Bearer synthetic"})
    accepted = destination in {"https://redis.example.test", "https://redis.example.test/"}

    async def original(client, request, **kwargs):
        assert accepted, "Unauthorised egress"
        return httpx.Response(200)

    if accepted:
        assert asyncio.run(guarded_async_send(original, None, request)).status_code == 200
    else:
        with pytest.raises(RuntimeError):
            asyncio.run(guarded_async_send(original, None, request))


def test_async_quota_shape_without_trailing_slash(monkeypatch):
    from deployment.phase5_redis import guarded_async_send
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://redis.example.test/")
    seen = []

    async def original(client, request, **kwargs):
        seen.append((request, kwargs))
        return httpx.Response(200, json={"result": [1, 60000]}, request=request)

    async def run():
        request = httpx.Request("POST", "https://redis.example.test", json=["EVAL", "synthetic", "1", "key"],
                                headers={"Authorization": "Bearer synthetic"})
        return await guarded_async_send(original, None, request, follow_redirects=True)

    assert asyncio.run(run()).json()["result"] == [1, 60000]
    assert seen[0][0].headers["Authorization"] == "Bearer synthetic"
    assert seen[0][1]["follow_redirects"] is False
