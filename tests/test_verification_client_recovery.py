"""Use the normal client for error injection; never transplant body-length headers."""

import json

import httpx
import pytest

from interview_app_frontend.services.api_client import BackendError, InterviewAPIClient
from tests.question_contract_fixtures import valid_bundle


def test_explicit_question_retry_preserves_identity_and_body_length(monkeypatch):
    monkeypatch.setenv("BACKEND_VISITOR_SIGNING_KEY", "")
    monkeypatch.setattr("interview_app_frontend.services.visitor.session_token", lambda key: "same-test-identity")
    requests = []

    def respond(request):
        requests.append(request)
        assert int(request.headers["Content-Length"]) == len(request.content)
        assert json.loads(request.content)["question_index"] == 2
        if len(requests) == 1:
            return httpx.Response(502, json={"error": {"code": "provider_failure"}})
        return httpx.Response(200, json=valid_bundle())

    client = InterviewAPIClient(base_url="https://synthetic.example", secret="synthetic-auth",
                                transport=httpx.MockTransport(respond))
    payload = {"role": "Backend Engineer", "question_index": 2, "question_list_count": 5,
               "focus": "PREVIEW_PROVIDER_ERROR"}
    with pytest.raises(BackendError):
        client.question(**payload)
    assert len(requests) == 1  # No automatic POST retry.
    payload["focus"] = ""
    assert len(client.question(**payload)["questions"]) == 5
    assert len(requests) == 2
    assert len(requests[0].content) != len(requests[1].content)
    assert {r.headers["X-Interview-Visitor"] for r in requests} == {"same-test-identity"}
