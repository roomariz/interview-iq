"""Exercise Streamlit session handlers through HTTP with mocked backend services."""

import ast
from concurrent.futures import Future
from pathlib import Path
from time import monotonic, sleep

import httpx
import pytest
import streamlit as st
from fastapi.testclient import TestClient

from api import interview
from api.index import app
from interview_app_frontend.services.api_client import InterviewAPIClient
from interview_app_frontend.state import session_manager as manager
from interview_app_frontend.state import question_generation_job as jobs
from interview_app_frontend.state import answer_evaluation_job as evaluations
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation


class APITransport(httpx.BaseTransport):
    def __init__(self, server):
        self.server = server

    def handle_request(self, request):
        response = self.server.request(request.method, str(request.url), content=request.content, headers=request.headers)
        return httpx.Response(response.status_code, content=response.content, headers=response.headers, request=request)


@pytest.fixture
def workflow(monkeypatch):
    monkeypatch.setenv("BACKEND_API_SECRET", "workflow-secret")
    monkeypatch.setenv("BACKEND_RATE_LIMIT", "1000")
    monkeypatch.setattr(interview.settings, "MODEL_NAME", "test:free")
    app.middleware_stack = None
    calls = []

    def question(**kwargs):
        calls.append(kwargs)
        return {"questions": [{"question": f'A service has slow requests in scenario {kwargs["question_index"]}. How would you diagnose the bottleneck?'}], "meta": {}}

    monkeypatch.setattr(interview.question_service, "get_next_question_for_session", question)
    monkeypatch.setattr(interview.evaluation_service, "evaluate_submission", build_relevance_gate_evaluation)
    with TestClient(app) as server:
        client = InterviewAPIClient(secret="workflow-secret", transport=APITransport(server))
        for module in (manager, jobs, evaluations):
            monkeypatch.setattr(module, "InterviewAPIClient", lambda: client)
        st.session_state.clear()
        manager.ensure_session_state()
        yield calls
        jobs.reset_question_generation_state(st.session_state)
        st.session_state.clear()


def wait_for_question():
    deadline = monotonic() + 5
    while monotonic() < deadline:
        if jobs.poll_question_generation(st.session_state):
            return
        sleep(0.01)
    pytest.fail("Question request did not finish")


def test_complete_interview_over_http(workflow):
    st.session_state.update(setup_role="Backend Engineer", setup_persona="Friendly", setup_difficulty="Easy",
                            setup_cv_content="Python API development", setup_job_description="Python SQL engineer")
    manager.start_interview()
    assert st.session_state.current_screen == "generating_question"
    for index in range(1, 4):
        wait_for_question()
        assert st.session_state.current_screen == "question"
        assert st.session_state.current_question_index == index
        st.session_state.answer = "I would measure the slow request, inspect the query plan and compare the result after the change."
        manager.submit_answer()
        future = st.session_state.get("answer_evaluation_future")
        if isinstance(future, Future):
            future.result(timeout=5)
            feedback = evaluations.consume_answer_evaluation(st.session_state)
            manager.finalise_answer_submission(st.session_state.current_question, st.session_state.answer, feedback)
        assert st.session_state.current_screen == "feedback"
        assert st.session_state.feedback["follow_up"]["question"]
        assert len(st.session_state.answers) == index
        manager.advance_to_next_question()
        if index < 3:
            jobs.begin_question_generation(st.session_state)
    manager.go_to_session_summary()
    assert st.session_state.current_screen == "summary"
    assert st.session_state.session_complete
    assert len(workflow) == 3
    assert workflow[1]["previous_questions"] == [st.session_state.answers[0]["question"]]
    assert workflow[0]["cv_context"] == "Python API development"
    assert workflow[0]["gap_analysis"]["has_gaps"]
    assert "cv_context" not in st.session_state.answers[0]


def test_session_defaults_and_question_requests_are_isolated(workflow):
    first = dict(st.session_state)
    first["answers"].append({"question": "Session one question?"})
    st.session_state.clear()
    manager.ensure_session_state()
    assert st.session_state.answers == []
    st.session_state.update(role="Data Engineer", current_question_index=1, difficulty="Easy", persona="Friendly", response_style="Concise")
    jobs.begin_question_generation(st.session_state)
    st.session_state.role = "Frontend Engineer"
    wait_for_question()
    assert workflow[0]["role"] == "Data Engineer"
    assert workflow[0]["previous_questions"] == []


def test_restart_does_not_apply_stale_question_result(workflow):
    st.session_state.update(role="Engineer", current_question_index=1, difficulty="Easy", persona="Friendly", response_style="Concise")
    jobs.begin_question_generation(st.session_state)
    manager.restart_session()
    assert not jobs.poll_question_generation(st.session_state)
    assert st.session_state.current_screen == "welcome"


def test_frontend_does_not_import_provider_or_business_services():
    violations = []
    for path in Path("interview_app_frontend").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("interview_app_backend.services", "interview_app_backend.llm", "config.settings", "config.model_profiles")):
                    violations.append(f"{path}:{node.lineno}")
    assert violations == []
