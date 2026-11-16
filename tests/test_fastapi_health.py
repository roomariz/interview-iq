from fastapi.testclient import TestClient

from api.index import app


def test_health_is_available_without_credentials(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"


def test_health_does_not_expose_interview_endpoints():
    with TestClient(app) as client:
        assert client.post("/api/health").status_code == 405
        assert client.post("/api/evaluate", json={}).status_code == 404
