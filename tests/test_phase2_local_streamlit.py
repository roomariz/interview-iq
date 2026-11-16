"""A real Streamlit script talks to a local Uvicorn HTTP server, with no LLM network."""

import socket
from threading import Thread
from time import monotonic, sleep

import uvicorn
from streamlit.testing.v1 import AppTest

from api.index import app
from api import interview
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation


def test_streamlit_interview_with_local_fastapi(monkeypatch):
    monkeypatch.setenv("BACKEND_API_SECRET", "loopback-test-secret")
    monkeypatch.setenv("BACKEND_RATE_LIMIT", "1000")
    monkeypatch.setenv("BACKEND_API_TIMEOUT", "10")
    monkeypatch.setattr(interview.settings, "MODEL_NAME", "test:free")
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return f'A service has slow requests in scenario {kwargs["question_index"]}. How would you diagnose the bottleneck?'

    monkeypatch.setattr(interview.question_service, "get_next_question_for_session", generate)
    monkeypatch.setattr(interview.evaluation_service, "evaluate_submission", build_relevance_gate_evaluation)
    app.middleware_stack = None
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    monkeypatch.setenv("BACKEND_API_URL", f"http://127.0.0.1:{listener.getsockname()[1]}")
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
    thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        deadline = monotonic() + 5
        while not server.started and monotonic() < deadline:
            sleep(0.01)
        assert server.started
        ui = AppTest.from_string(
            "import streamlit as st\n"
            "from interview_app_frontend.state.session_manager import start_interview\n"
            "from interview_app_frontend.app import main\n"
            "if st.session_state.pop('_test_start', False):\n"
            "    start_interview()\n"
            "main()\n", default_timeout=10,
        ).run()
        assert not ui.exception
        assert ui.button(key="welcome_start_setup")
        # Streamlit 1.40's AppTest cannot serialise segmented_control state.
        # Supply the same setup values to its normal callback, then test rendered screens.
        for key, value in {"setup_role": "Backend Engineer", "setup_persona": "Friendly",
                           "setup_difficulty": "Easy", "_test_start": True}.items():
            ui.session_state[key] = value
        ui.run()
        for index in range(1, 4):
            future = ui.session_state["question_generation_future"]
            if future:
                future.result(timeout=5)
                ui.run()
            assert not ui.exception
            assert ui.session_state["current_screen"] == "question"
            ui.text_area(key="answer").input(
                "I would measure slow requests, identify the bottleneck and verify improvements with a representative test."
            ).run()
            ui.button(key="question_submit_answer").click().run()
            future = ui.session_state["answer_evaluation_future"]
            if future:
                future.result(timeout=5)
                ui.run()
            assert not ui.exception
            assert ui.session_state["current_screen"] == "feedback"
            ui.button(key="feedback_next_question").click().run()
        assert ui.session_state["current_screen"] == "summary"
        assert len(ui.session_state["answers"]) == 3
        assert len(calls) == 3
        assert calls[1]["previous_questions"]
        assert not ui.exception
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
