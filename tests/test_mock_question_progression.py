"""Reproduce fixed-fixture rejection and verify the replacement's real validators."""

import json

import pytest
from fastapi.testclient import TestClient

from api import interview
from api.index import app
from deployment.mock_questions import REQUEST, bind_request, question_bundle
from tests.mock_question_support import configure_questions
from tests.question_contract_fixtures import valid_bundle


@pytest.fixture
def connection(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("BACKEND_API_SECRET", "mock-progression-test")
    monkeypatch.setenv("BACKEND_RATE_LIMIT", "1000")
    monkeypatch.setenv("BACKEND_VISITOR_SIGNING_KEY", "")
    monkeypatch.setenv("BACKEND_RATE_BACKEND", "memory")
    app.middleware_stack = None
    with TestClient(app) as client:
        yield client, {"Authorization": "Bearer mock-progression-test"}


def test_original_fixed_fixture_reproduces_second_request_502(connection, monkeypatch):
    client, headers = connection
    configure_questions(monkeypatch)
    attempts = []
    def fixed(*args, **kwargs):
        attempts.append(kwargs["task"])
        return json.dumps(valid_bundle())
    monkeypatch.setattr(interview.question_service, "call_llm", fixed)
    payload = {"role": "Backend Engineer", "question_list_count": 5}
    first = client.post("/api/interview/question", headers=headers, json=payload)
    assert first.status_code == 200
    with pytest.raises(RuntimeError, match="Fallback generation failed validation: question\\[1\\]: duplicate_previous_question"):
        interview.question_service.get_next_question_for_session(
            **payload, difficulty="Easy", persona="Friendly", response_style="Detailed", focus="",
            cv_context="", question_index=2, previous_questions=[first.json()["questions"][0]["question"]])
    response = client.post("/api/interview/question", headers=headers, json={
        **payload, "question_index": 2, "previous_questions": [first.json()["questions"][0]["question"]]})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "provider_failure"
    assert "duplicate_previous_question" not in response.text
    assert len(attempts) == 7  # One success; two reproductions with three rejected attempts each.


@pytest.mark.parametrize("count", [1, 5])
@pytest.mark.parametrize("cv,jd", [
    ("", ""), ("Python API", "Python API reliability"),
    ("Built a synthetic Python REST API with PostgreSQL and unit tests.",
     "Maintain Python APIs, PostgreSQL queries and reliable releases."),
])
def test_five_adaptive_requests_pass_real_question_validation(connection, monkeypatch, count, cv, jd):
    client, headers = connection
    requests, attempts = configure_questions(monkeypatch, count=count)
    previous = []
    for index in range(1, 6):
        response = client.post("/api/interview/question", headers=headers, json={
            "role": "Backend Engineer", "cv_context": cv, "jd_context": jd,
            "question_index": index, "question_list_count": count, "previous_questions": previous[-3:]})
        assert response.status_code == 200, response.text
        items = response.json()["questions"]
        assert len(items) == count
        assert [item["sequence_order"] for item in items] == list(range(1, count + 1))
        question = items[0]["question"]
        assert question not in previous
        previous.append(question)
    assert attempts == [1, 2, 3, 4, 5]
    assert [request["question_index"] for request in requests] == attempts
    assert REQUEST.get() is None


def test_mock_request_context_is_reset_after_error():
    def fail(**kwargs):
        assert REQUEST.get()["question_index"] == 2
        raise ValueError("synthetic")
    with pytest.raises(ValueError):
        bind_request(fail)(question_index=2)
    assert REQUEST.get() is None


@pytest.mark.parametrize("payload", [None, {"question_index": 6}, {"question_list_count": 0}])
def test_mock_exhaustion_is_explicit(payload):
    with pytest.raises(RuntimeError):
        question_bundle(payload)
