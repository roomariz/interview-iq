"""Adapt existing UI tests' service doubles to the new HTTP boundary.

The original assertions and injected questions stay unchanged. Generation is
completed inside each test's patch scope, so HTTP workers cannot outlive mocks.
"""

import json

import httpx

from api.interview import context
from interview_app_backend.services import question_generation_job as legacy_jobs
from interview_app_frontend.services.api_client import InterviewAPIClient
from interview_app_frontend.state import question_generation_job as jobs
from interview_app_frontend.state import session_manager
from shared.api_contracts import ContextRequest

LEGACY_UI_TESTS = {
    "test_question_topics_are_persisted_after_start",
    "test_start_interview_uses_llm_generated_question",
    "test_question_screen_renders_answer_layout",
    "test_question_screen_renders_generic_fallback_without_multiline_cv_or_jd_text",
    "test_question_screen_renders_warning_banner",
}


def configure_http_double(request, monkeypatch):
    def handle(http_request):
        payload = json.loads(http_request.content)
        if http_request.url.path.endswith("/context"):
            return httpx.Response(200, json=context(ContextRequest(**payload)).model_dump())
        result = legacy_jobs.get_next_question_for_session(**payload, return_meta=True)
        if isinstance(result, str):
            result = {"questions": [{"question": result}], "meta": {}}
        elif isinstance(result, list):
            result = {"questions": result, "meta": {}}
        return httpx.Response(200, json=result)

    client = InterviewAPIClient(secret="local-test", transport=httpx.MockTransport(handle))
    monkeypatch.setattr(session_manager, "InterviewAPIClient", lambda: client)
    monkeypatch.setattr(jobs, "InterviewAPIClient", lambda: client)

    def begin(state):
        jobs.begin_question_generation(state)
        state["question_generation_future"].result(timeout=5)

    monkeypatch.setattr(session_manager, "begin_question_generation", begin)
    if hasattr(request.module, "_wait_for_generation"):
        monkeypatch.setattr(request.module, "poll_question_generation", jobs.poll_question_generation)
