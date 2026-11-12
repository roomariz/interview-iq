from concurrent.futures import Future
import logging
import sys
from threading import Event
from time import sleep, time
from unittest.mock import MagicMock, patch

import streamlit as st

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

from interview_app_frontend.components.question_screen import render_question_and_answer
from interview_app_backend.services.question_generation_job import poll_question_generation
from interview_app_backend.services.question_generation_job import MAX_WAIT_SECONDS
from interview_app_backend.services.question_generation_job import _finalise_question_job
from interview_app_frontend.state.session_manager import start_interview
from interview_app_backend.llm import provider_fallback
from interview_app_backend.llm.provider_fallback import call_llm_with_fallback


def _wait_for_generation(timeout: float = 1.0) -> None:
    deadline = time() + timeout
    while time() < deadline:
        if poll_question_generation(st.session_state):
            return
        sleep(0.01)


def test_question_screen_renders_generic_fallback_without_multiline_cv_or_jd_text():
    st.session_state.clear()
    st.session_state.setup_role = "Full Stack Engineer"
    st.session_state.setup_persona = "Friendly"
    st.session_state.setup_difficulty = "Easy"
    st.session_state.setup_response_style = "Concise"
    st.session_state.setup_cv_content = "PROFESSIONAL HIGHLIGHTS\nSenior Full Stack Engineer"
    st.session_state.setup_job_description = "Senior Full Stack Engineer (Java / Angular)\nLocation: Frankfurt am Main"

    with patch(
        "interview_app_backend.services.question_generation_job.get_next_question_for_session",
        return_value="You are working on a full stack engineer team and users report that a recent change caused a visible regression. How would you investigate the issue, prioritise fixes, and explain the outcome?",
    ):
        start_interview()
    _wait_for_generation()

    assert st.session_state.current_question == (
        "You are working on a full stack engineer team and users report that a recent change caused a visible regression. How would you investigate the issue, prioritise fixes, and explain the outcome?"
    )
    assert "\n" not in st.session_state.current_question
    assert "professional highlights" not in st.session_state.current_question.lower()
    assert "location:" not in st.session_state.current_question.lower()

    with patch("interview_app_frontend.components.question_screen.render_interview_sidebar"), patch(
        "interview_app_frontend.components.question_screen.render_shared_topbar"
    ), patch("interview_app_frontend.components.question_panel.st.markdown") as mock_markdown, patch(
        "interview_app_frontend.components.question_panel.st.columns"
    ) as mock_columns, patch(
        "interview_app_frontend.components.question_panel.st.button"
    ), patch(
        "interview_app_frontend.components.question_panel.st.text_area"
    ) as mock_text_area, patch(
        "interview_app_frontend.components.question_panel.st.container"
    ) as mock_container:
        mock_columns.side_effect = lambda spec, **kwargs: tuple(MagicMock() for _ in range(len(spec)))
        mock_container.return_value.__enter__.return_value = MagicMock()
        mock_container.return_value.__exit__.return_value = False
        render_question_and_answer()

    rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args).lower()
    assert "you are working on a full stack engineer team" in rendered_html
    assert "professional highlights" not in rendered_html
    assert "frankfurt am main" not in rendered_html
    assert "distribution" not in rendered_html
    assert mock_text_area.call_args.kwargs["key"] == "answer"


def test_locked_question_screen_shows_submitted_answer_expander():
    st.session_state.clear()
    st.session_state.current_question = "Describe a time you improved system performance under constraints."
    st.session_state.answer = "I reduced latency from 400ms to 120ms by profiling the bottleneck."
    st.session_state.answer_evaluation_notice = "Evaluating your answer now. We are checking relevance, evidence, and scoring."

    with patch("interview_app_frontend.components.question_screen.render_interview_sidebar"), patch(
        "interview_app_frontend.components.question_screen.render_shared_topbar"
    ), patch("interview_app_frontend.components.question_screen.render_loading_indicator") as mock_loading, patch(
        "interview_app_frontend.components.question_screen.render_question_panel"
    ) as mock_question_panel, patch(
        "interview_app_frontend.components.question_screen.render_prepared_questions_panel"
    ) as mock_prepared_questions, patch("interview_app_frontend.components.question_screen.st.markdown"), patch(
        "interview_app_frontend.components.question_screen.st.write"
    ), patch("interview_app_frontend.components.question_screen.st.info"), patch(
        "interview_app_frontend.components.question_screen.st.expander"
    ) as mock_expander:
        mock_expander.return_value.__enter__.return_value = None
        mock_expander.return_value.__exit__.return_value = False
        render_question_and_answer(locked=True)

    mock_question_panel.assert_not_called()
    mock_prepared_questions.assert_not_called()
    assert mock_expander.call_args.args[0] == "Your Answer (submitted)"
    mock_loading.assert_called()
    assert mock_loading.call_args.args[0] == "Evaluation in progress"
    assert mock_loading.call_args.kwargs.get("compact") is True


def test_question_screen_does_not_render_duplicate_question_heading():
    st.session_state.clear()
    st.session_state.current_question = "Describe a time you improved system performance under constraints."
    st.session_state.prepared_questions = [{"sequence_order": 1, "question": "Describe a time you improved system performance under constraints."}]
    st.session_state.question_meta = {"total_questions": 1}

    with patch("interview_app_frontend.components.question_screen.render_interview_sidebar"), patch(
        "interview_app_frontend.components.question_screen.render_shared_topbar"
    ), patch("interview_app_frontend.components.question_screen.render_prepared_questions_panel") as mock_prepared_questions_panel, patch(
        "interview_app_frontend.components.question_screen.render_question_panel"
    ), patch("interview_app_frontend.components.question_screen.st.markdown") as mock_markdown, patch(
        "interview_app_frontend.components.question_screen.st.info"
    ):
        render_question_and_answer()

    rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
    assert "### Question" not in rendered_html
    assert "Question generated with" not in rendered_html
    mock_prepared_questions_panel.assert_not_called()


def test_question_generation_timeout_recovery_uses_backup_question(caplog):
    st.session_state.clear()
    st.session_state.setup_role = "Backend Engineer"
    st.session_state.setup_persona = "Friendly"
    st.session_state.setup_difficulty = "Easy"
    st.session_state.setup_response_style = "Concise"
    st.session_state.setup_cv_content = "Spring Boot"
    st.session_state.setup_job_description = "Backend role"
    st.session_state.question_generation_future = Future()
    st.session_state.question_job = {"status": "running", "result": None, "error": None, "started_at": time() - MAX_WAIT_SECONDS - 1}
    st.session_state.generation_start_time = time() - MAX_WAIT_SECONDS - 1

    with patch(
        "interview_app_backend.services.question_generation_job.generate_fallback_question",
        return_value="You are working on a backend team where a recent release caused a regression. How would you investigate and fix it?",
    ), caplog.at_level(logging.WARNING, logger="interview_app_backend.services.question_generation_job"):
        recovered = poll_question_generation(st.session_state)

    assert recovered is True
    assert st.session_state.current_screen == "question"
    assert st.session_state.current_question.startswith("You are working on a backend team")
    assert st.session_state.question_job["status"] == "timeout"
    assert "We prepared a backup question to keep your session smooth." in st.session_state.question_generation_notice
    assert "Question generation fallback root cause: reason=timeout_exceeded" in caplog.text
    assert "exceeded wait limit" in caplog.text


def test_question_generation_failure_recovery_uses_backup_question(caplog):
    st.session_state.clear()
    st.session_state.setup_role = "Backend Engineer"
    st.session_state.setup_persona = "Friendly"
    st.session_state.setup_difficulty = "Easy"
    st.session_state.setup_response_style = "Concise"
    st.session_state.setup_cv_content = "Spring Boot"
    st.session_state.setup_job_description = "Backend role"
    future = Future()
    future.set_exception(RuntimeError("boom"))
    st.session_state.question_generation_future = future
    st.session_state.question_job = {"status": "running", "result": None, "error": None, "started_at": time()}
    st.session_state.generation_start_time = time()

    with patch(
        "interview_app_backend.services.question_generation_job.generate_fallback_question",
        return_value="You are working on a backend team where a recent release caused a regression. How would you investigate and fix it?",
    ), caplog.at_level(logging.WARNING, logger="interview_app_backend.services.question_generation_job"):
        recovered = poll_question_generation(st.session_state)

    assert recovered is True
    assert st.session_state.current_screen == "question"
    assert st.session_state.question_job["status"] == "failed"
    assert "We prepared a backup question to keep your session smooth." in st.session_state.question_generation_notice
    assert "Question generation fallback root cause: reason=future_exception" in caplog.text
    assert "boom" in caplog.text


def test_timeout_fallback_is_not_overwritten_by_late_completion():
    st.session_state.clear()
    st.session_state.question_job = {"status": "timeout", "result": "Fallback question", "error": "timeout", "started_at": time()}
    st.session_state.current_question = "Fallback question"
    st.session_state.current_screen = "question"
    st.session_state.launch_question_view = False
    st.session_state.has_active_session = True

    _finalise_question_job(
        st.session_state,
        {"question_plan": {"started_at": time()}},
        "Late LLM question should not replace the fallback.",
        status="completed",
        allow_current_question_update=False,
    )

    assert st.session_state.current_question == "Fallback question"


def test_cancelled_question_generation_stops_before_client_lookup():
    cancel_event = Event()
    cancel_event.set()

    with patch("interview_app_backend.llm.provider_fallback.get_openrouter_client") as mock_client:
        response, call_log = call_llm_with_fallback("prompt", should_abort=cancel_event.is_set)

    assert response is None
    assert call_log.fallback_reason == "cancelled"
    mock_client.assert_not_called()


def test_question_generation_uses_one_openrouter_model():
    st.session_state.clear()
    st.session_state.setup_role = "Backend Engineer"
    st.session_state.setup_persona = "Friendly"
    st.session_state.setup_difficulty = "Easy"
    st.session_state.setup_response_style = "Concise"
    st.session_state.setup_cv_content = "Spring Boot"
    st.session_state.setup_job_description = "Backend role"

    response_payload = (
        '{"questions":[{"sequence_order":1,"question":"Single model question","question_type":"technical","focus_area":"performance",'
        '"source_basis":{"cv_terms_used":[],"jd_terms_used":[],"gap_used":null},"difficulty_level":"Easy",'
        '"what_interviewer_is_testing":["Performance investigation"]}],"meta":{"total_questions":1,"distribution":'
        '{"cv_based":0,"jd_based":0,"behavioural":0,"deep_dive":0,"gap_targeted":1}}}'
    )

    with patch.object(provider_fallback.PROVIDER_CONFIGS["open-router"], "api_key_getter", return_value="configured-key"), patch.object(
        provider_fallback.PROVIDER_CONFIGS["open-router"],
        "client_getter",
        return_value=object(),
    ), patch.object(provider_fallback.PROVIDER_CONFIGS["grok"], "api_key_getter") as mock_grok_key, patch.object(
        provider_fallback.PROVIDER_CONFIGS["grok"],
        "client_getter",
    ) as mock_grok_client, patch.object(provider_fallback.PROVIDER_CONFIGS["google"], "api_key_getter") as mock_google_key, patch.object(
        provider_fallback.PROVIDER_CONFIGS["google"],
        "client_getter",
    ) as mock_google_client, patch(
        "interview_app_backend.llm.provider_fallback._call_openrouter",
        return_value=response_payload,
    ) as mock_call:
        response, call_log = call_llm_with_fallback("prompt", max_models_per_provider=1)

    assert response == response_payload
    assert call_log.response_valid is True
    assert mock_call.call_args.kwargs["max_models_per_provider"] == 1
    mock_grok_key.assert_not_called()
    mock_grok_client.assert_not_called()
    mock_google_key.assert_not_called()
    mock_google_client.assert_not_called()
