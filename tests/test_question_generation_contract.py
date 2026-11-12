import json
from concurrent.futures import Future
from time import time

import streamlit as st

from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt
from interview_app_backend.llm.question_generation_parser import parse_question_generation_response
from interview_app_backend.services.question_generation_job import QUESTION_GENERATION_FUTURE
from interview_app_backend.services.question_generation_job import QUESTION_GENERATION_READY
from interview_app_backend.services.question_generation_job import QUESTION_GENERATION_STARTED_AT
from interview_app_backend.services.question_generation_job import QUESTION_JOB_KEY
from interview_app_backend.services.question_generation_job import poll_question_generation


def test_free_mode_prompt_requests_a_single_item_array() -> None:
    prompt = build_question_generation_prompt(
        role="Backend Engineer",
        difficulty="Medium",
        persona="Strict",
        response_style="Concise",
        temperature=0.7,
        cv_profile="Python",
        job_description="API role",
        gap_analysis={},
        prompt_style="simple",
    )

    assert "Return a JSON array with exactly ONE question object." in prompt
    assert "Keep the array shape even when there is only one question." in prompt


def test_question_generation_parser_normalises_single_object_to_list() -> None:
    payload = json.dumps({"question": "How would you improve API performance?", "type": "technical", "focus": "performance"})

    parsed = parse_question_generation_response(payload, strict=False)

    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["question"] == "How would you improve API performance?"


def test_empty_question_generation_response_stops_flow_cleanly() -> None:
    st.session_state.clear()
    st.session_state.question_generation_future = Future()
    st.session_state.question_generation_future.set_result(
        {"token": 1, "questions": [], "meta": {}, "llm_metadata": {}}
    )
    st.session_state.question_job = {"status": "running", "result": None, "error": None, "started_at": time()}
    st.session_state.question_generation_started_at = time()
    st.session_state.generation_start_time = time()
    st.session_state.question_generation_ready = True
    st.session_state.current_screen = "generating_question"

    assert poll_question_generation(st.session_state) is True
    assert st.session_state.current_screen == "setup"
    assert st.session_state.setup_error == "Model unavailable"
    assert st.session_state.question_job["status"] == "failed"
    assert st.session_state[QUESTION_GENERATION_FUTURE] is None
    assert st.session_state[QUESTION_GENERATION_READY] is False
    assert st.session_state[QUESTION_GENERATION_STARTED_AT] is None
    assert st.session_state[QUESTION_JOB_KEY]["error"] == "Model unavailable"
