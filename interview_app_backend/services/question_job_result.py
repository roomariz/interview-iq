"""Question generation job result."""
from __future__ import annotations

from interview_app_backend.services import question_generation_job as _job_api


def _finalise_question_job(
    state: _job_api.Any,
    payload: dict[str, _job_api.Any],
    questions: _job_api.Any,
    status: str,
    error: str | None = None,
    notice: str = "",
    allow_current_question_update: bool = True,
    meta: dict[str, _job_api.Any] | None = None,
    llm_metadata: dict[str, _job_api.Any] | None = None,
) -> bool:
    _job_api._stop_question_generation(state)
    if not questions:
        return _fail_question_generation(state)
    started_at = payload.get("started_at") or _job_api._state_value(state, _job_api.QUESTION_GENERATION_STARTED_AT, None) or payload["question_plan"].get("started_at")
    prepared_questions = [item for item in questions if isinstance(item, dict)] if isinstance(questions, list) else ([{"question": questions.strip()}] if isinstance(questions, str) and questions.strip() else [])
    question_text = str(prepared_questions[0].get("question", "")).strip() if prepared_questions else (questions.strip() if isinstance(questions, str) else "")
    question_meta = meta or _job_api._build_question_meta(prepared_questions)
    if allow_current_question_update:
        state["current_question"] = question_text
    state["prepared_questions"] = prepared_questions
    state["base_questions"] = list(prepared_questions)
    state["follow_up_questions"] = list(state.get("follow_up_questions", []))
    state["question_meta"] = question_meta
    llm_metadata = llm_metadata or {}
    state["question_generation_model"] = str(llm_metadata.get("model", "")).strip()
    state["question_generation_provider"] = str(llm_metadata.get("provider", "")).strip()
    state["question_generation_task"] = str(llm_metadata.get("task", "")).strip()
    state["current_screen"] = "question"
    state["launch_question_view"] = True
    state["has_active_session"] = True
    state["is_loading"] = False
    state["question_generation_notice"] = notice
    state["question_generation_error"] = error or ""
    state[_job_api.QUESTION_GENERATION_FUTURE] = None
    state[_job_api.QUESTION_GENERATION_STARTED_AT] = None
    state["generation_start_time"] = None
    state[_job_api.QUESTION_GENERATION_READY] = True
    state[_job_api.QUESTION_JOB_KEY] = {
        "status": status,
        "result": prepared_questions,
        "error": error,
        "started_at": started_at,
        "llm_metadata": llm_metadata,
    }
    _job_api.LOGGER.info(
        "Question distribution: %s provider=%s model=%s task=%s",
        question_meta["distribution"],
        state["question_generation_provider"] or "unknown",
        state["question_generation_model"] or "unknown",
        state["question_generation_task"] or "unknown",
    )
    topic = _job_api.extract_topic(state["current_question"])
    if topic:
        existing_topics = [str(item).strip().lower() for item in state.get("question_topics", [])]
        if topic not in existing_topics:
            state["question_topics"] = [*state.get("question_topics", []), topic][-8:]
    return True


def _recover_with_fallback(state: _job_api.Any, payload: dict[str, _job_api.Any], status: str, notice: str) -> bool:
    _job_api._stop_question_generation(state)
    fallback_bundle = _job_api._build_fallback_questions(payload)
    state["question_generation_notice"] = notice
    return _job_api._finalise_question_job(
        state,
        payload,
        fallback_bundle["questions"],
        status=status,
        error=notice,
        notice=notice,
        meta=fallback_bundle["meta"],
        llm_metadata={},
    )


def _log_root_cause(reason: str, payload: dict[str, _job_api.Any], *, status: str, elapsed_seconds: float | None = None, error: str = "") -> None:
    elapsed_part = f"{elapsed_seconds:.2f}s" if elapsed_seconds is not None else "unknown"
    _job_api.LOGGER.warning(
        "Question generation fallback root cause: reason=%s status=%s elapsed=%s role=%s difficulty=%s question_type=%s error=%s",
        reason,
        status,
        elapsed_part,
        payload["role"] or "unknown",
        payload["difficulty"] or "unknown",
        payload["question_type"] or "unknown",
        error or "none",
    )



def _fail_question_generation(state) -> bool:
    message = "Model unavailable"
    state[_job_api.QUESTION_JOB_KEY] = {"status": "failed", "result": [], "error": message, "started_at": None}
    for key in [_job_api.QUESTION_GENERATION_ERROR, _job_api.QUESTION_GENERATION_NOTICE, "setup_error"]:
        state[key] = message
    for key in [_job_api.QUESTION_GENERATION_FUTURE, _job_api.QUESTION_GENERATION_STARTED_AT, "generation_start_time"]:
        state[key] = None
    for key in [_job_api.QUESTION_GENERATION_READY, "is_loading", "launch_question_view", "has_active_session"]:
        state[key] = False
    state["current_screen"] = "setup"
    return True
