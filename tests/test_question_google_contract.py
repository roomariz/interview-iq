import json

import httpx
from openai import OpenAI

from config import settings
from interview_app_backend.services import question_service as service
from question_contract_fixtures import valid_bundle


def test_google_sdk_retries_partial_bundle_with_exact_schema_and_feedback(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "google")
    monkeypatch.setattr(service, "MODEL_NAME", "gemini-3.5-flash-lite")
    captured = []
    partial = valid_bundle()
    partial["questions"] = partial["questions"][:1]
    responses = [partial, valid_bundle()]

    def respond(request):
        captured.append(json.loads(request.content))
        payload = responses.pop(0)
        return httpx.Response(200, json={
            "id": "question-test", "object": "chat.completion", "created": 0,
            "model": "gemini-3.5-flash-lite",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps(payload),
            }}],
        })

    with OpenAI(api_key="test-key", base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        monkeypatch.setattr(service, "get_openrouter_client", lambda: client)
        bundle = service.get_next_question_for_session(
            role="Backend Engineer", difficulty="Medium", persona="Friendly", response_style="Concise",
            focus="General", cv_context="", jd_context="", question_index=1,
            question_list_count=5, return_meta=True,
        )
    assert bundle == valid_bundle()
    assert len(captured) == 2
    for request in captured:
        assert request["response_format"]["type"] == "json_schema"
        bounds = request["response_format"]["json_schema"]["schema"]["properties"]["questions"]
        assert bounds["minItems"] == bounds["maxItems"] == 5
    assert "invalid_question_count: expected 5, received 1" in captured[1]["messages"][0]["content"]
