"""Question generation job payload."""
from __future__ import annotations

from copy import deepcopy

from interview_app_backend.services import question_generation_job as _job_api


def _state_value(state: _job_api.Any, key: str, fallback: _job_api.Any = "") -> _job_api.Any:
    if hasattr(state, "get"):
        return state.get(key, fallback)
    return getattr(state, key, fallback)


def _default_question_job(status: str = "pending", result: _job_api.Any = None, error: _job_api.Any = None, started_at: _job_api.Any = None) -> dict[str, _job_api.Any]:
    return {"status": status, "result": result, "error": error, "started_at": started_at}


def _ensure_question_job(state: _job_api.Any) -> dict[str, _job_api.Any]:
    job = _job_api._state_value(state, _job_api.QUESTION_JOB_KEY, None)
    if not isinstance(job, dict):
        job = _job_api._default_question_job()
        state[_job_api.QUESTION_JOB_KEY] = job
    job.setdefault("status", "pending")
    job.setdefault("result", None)
    job.setdefault("error", None)
    job.setdefault("started_at", None)
    return job


def _question_generation_is_cancelled(state: _job_api.Any | None = None) -> bool:
    if state is None:
        return False
    cancel_event = _job_api._state_value(state, _job_api.QUESTION_GENERATION_CANCEL_EVENT, None)
    return bool(isinstance(cancel_event, _job_api.Event) and cancel_event.is_set())


def _stop_question_generation(state: _job_api.Any) -> None:
    cancel_event = _job_api._state_value(state, _job_api.QUESTION_GENERATION_CANCEL_EVENT, None)
    if isinstance(cancel_event, _job_api.Event):
        cancel_event.set()
    future = _job_api._state_value(state, _job_api.QUESTION_GENERATION_FUTURE, None)
    if isinstance(future, _job_api.Future):
        future.cancel()


def _build_payload(state: _job_api.Any) -> dict[str, _job_api.Any]:
    try:
        temperature = float(_job_api._state_value(state, "temperature", 0.7) or 0.7)
    except (TypeError, ValueError):
        temperature = 0.7
    previous_questions = []
    for entry in list(_job_api._state_value(state, "answers", []) or []):
        if isinstance(entry, dict):
            question = str(entry.get("question", "")).strip()
            if question:
                previous_questions.append(question)
    question_plan = _job_api.select_question_plan(state)
    question_count = _job_api.get_question_count(_job_api.MODEL_NAME)
    cancel_event = _job_api._state_value(state, _job_api.QUESTION_GENERATION_CANCEL_EVENT, None)
    return {
        "token": int(_job_api._state_value(state, _job_api.QUESTION_GENERATION_TOKEN, 0)),
        "role": str(_job_api._state_value(state, "role", "")).strip(),
        "difficulty": str(_job_api._state_value(state, "difficulty", "")).strip(),
        "persona": str(_job_api._state_value(state, "persona", "")).strip(),
        "response_style": str(_job_api._state_value(state, "response_style", "")).strip(),
        "temperature": temperature,
        "cv_context": str(_job_api._state_value(state, "setup_cv_content", "")).strip(),
        "jd_context": str(_job_api._state_value(state, "setup_job_description", "")).strip(),
        "gap_analysis": deepcopy(_job_api._state_value(state, "gap_analysis", {}) or {}),
        "asked_topics": list(_job_api._state_value(state, "question_topics", []) or []),
        "focus": str(_job_api._state_value(state, "setup_focus", "")).strip(),
        "tech_stack": list(_job_api._state_value(state, "tech_stack", []) or []),
        "competencies": list(_job_api._state_value(state, "competencies", []) or []),
        "question_type": str(_job_api._state_value(state, "question_type", "auto")).strip(),
        "previous_questions": previous_questions[-3:],
        "question_index": int(_job_api._state_value(state, "current_question_index", 1) or 1),
        "question_plan": question_plan,
        "question_list_count": 1 if _job_api.is_free_model(_job_api.MODEL_NAME) else question_count,
        "should_abort": cancel_event.is_set if isinstance(cancel_event, _job_api.Event) else None,
    }


def _build_question_meta(questions: list[dict[str, _job_api.Any]] | None) -> dict[str, _job_api.Any]:
    distribution = {key: 0 for key in ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")}
    prepared = [item for item in questions or [] if isinstance(item, dict)]
    for item in prepared:
        question_type = str(item.get("question_type", "")).strip()
        if question_type in distribution:
            distribution[question_type] += 1
    return {"total_questions": len(prepared), "distribution": distribution}


def _build_fallback_questions(payload: dict[str, _job_api.Any]) -> dict[str, _job_api.Any]:
    from interview_app_backend.services import question_service

    count = int(payload.get("question_list_count") or 5)
    try:
        if count > 1:
            questions = question_service.fallback_questions(
                role=payload["role"], difficulty=payload["difficulty"], focus=payload["focus"],
                cv_context=payload["cv_context"], jd_context=payload["jd_context"],
                question_type=payload["question_type"], previous_questions=payload["previous_questions"],
                question_plan=payload["question_plan"], required_count=count,
            )
        else:
            question = _job_api.generate_fallback_question(
                role=payload["role"], difficulty=payload["difficulty"], focus=payload["focus"],
                cv_context=payload["cv_context"], jd_context=payload["jd_context"],
                question_type=payload["question_type"], previous_questions=payload["previous_questions"],
                question_plan=payload["question_plan"],
            )
            valid, reason = question_service._validate_single_question(
                question, role=payload["role"], cv_context=payload["cv_context"], jd_context=payload["jd_context"],
                focus=payload["focus"], question_type=payload["question_type"],
            )
            if not valid or question_service._is_similar_to_previous(question, payload["previous_questions"]):
                raise RuntimeError(reason if not valid else "duplicate_previous_question")
            questions = [question_service._question_item(question, payload["question_plan"])]
    except (RuntimeError, ValueError) as exc:
        _job_api.LOGGER.warning("Fallback rejected: %s", exc)
        questions = []
    return {"questions": questions, "meta": _job_api._build_question_meta(questions)}
