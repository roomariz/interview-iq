from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from time import time
from threading import Event
from typing import Any

from interview_app_backend.services.question_service import extract_topic
from interview_app_backend.services.question_service import generate_fallback_question
from interview_app_backend.services.question_service import get_next_question_for_session
from interview_app_backend.services.question_sequence import select_question_plan
from config.model_profiles import get_question_count
from config.model_profiles import is_free_model
from interview_app_backend.llm.client import clear_last_llm_call_metadata
from interview_app_backend.llm.client import get_last_llm_call_metadata
from config.settings import MODEL_NAME


QUESTION_GENERATION_TOKEN = "question_generation_token"
QUESTION_GENERATION_FUTURE = "question_generation_future"
QUESTION_GENERATION_STARTED_AT = "question_generation_started_at"
QUESTION_GENERATION_ERROR = "question_generation_error"
QUESTION_GENERATION_READY = "question_generation_ready"
QUESTION_GENERATION_NOTICE = "question_generation_notice"
QUESTION_GENERATION_CANCEL_EVENT = "question_generation_cancel_event"
QUESTION_JOB_KEY = "question_job"
MAX_WAIT_SECONDS = 30
VALID_TRANSITIONS = {"pending": ["running"], "running": ["completed", "failed", "timeout"], "failed": [], "completed": [], "timeout": []}
BACKUP_NOTICE = "We prepared a backup question to keep your session smooth."
LOGGER = logging.getLogger(__name__)


def update_status(current: str, new: str) -> str:
    assert new in VALID_TRANSITIONS[current]
    return new
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="question-generation")
def _state_value(state: Any, key: str, fallback: Any = "") -> Any:
    if hasattr(state, "get"):
        return state.get(key, fallback)
    return getattr(state, key, fallback)
def _default_question_job(status: str = "pending", result: Any = None, error: Any = None, started_at: Any = None) -> dict[str, Any]:
    return {"status": status, "result": result, "error": error, "started_at": started_at}
def _ensure_question_job(state: Any) -> dict[str, Any]:
    job = _state_value(state, QUESTION_JOB_KEY, None)
    if not isinstance(job, dict):
        job = _default_question_job()
        state[QUESTION_JOB_KEY] = job
    job.setdefault("status", "pending")
    job.setdefault("result", None)
    job.setdefault("error", None)
    job.setdefault("started_at", None)
    return job


def _question_generation_is_cancelled(state: Any | None = None) -> bool:
    if state is None:
        return False
    cancel_event = _state_value(state, QUESTION_GENERATION_CANCEL_EVENT, None)
    return bool(isinstance(cancel_event, Event) and cancel_event.is_set())


def _stop_question_generation(state: Any) -> None:
    cancel_event = _state_value(state, QUESTION_GENERATION_CANCEL_EVENT, None)
    if isinstance(cancel_event, Event):
        cancel_event.set()
    future = _state_value(state, QUESTION_GENERATION_FUTURE, None)
    if isinstance(future, Future):
        future.cancel()
def _build_payload(state: Any) -> dict[str, Any]:
    try:
        temperature = float(_state_value(state, "temperature", 0.7) or 0.7)
    except (TypeError, ValueError):
        temperature = 0.7
    previous_questions = []
    for entry in list(_state_value(state, "answers", []) or []):
        if isinstance(entry, dict):
            question = str(entry.get("question", "")).strip()
            if question:
                previous_questions.append(question)
    question_plan = select_question_plan(state)
    question_count = get_question_count(MODEL_NAME)
    return {
        "token": int(_state_value(state, QUESTION_GENERATION_TOKEN, 0)),
        "role": str(_state_value(state, "role", "")).strip(),
        "difficulty": str(_state_value(state, "difficulty", "")).strip(),
        "persona": str(_state_value(state, "persona", "")).strip(),
        "response_style": str(_state_value(state, "response_style", "")).strip(),
        "temperature": temperature,
        "cv_context": str(_state_value(state, "setup_cv_content", "")).strip(),
        "jd_context": str(_state_value(state, "setup_job_description", "")).strip(),
        "gap_analysis": _state_value(state, "gap_analysis", {}) or {},
        "asked_topics": list(_state_value(state, "question_topics", []) or []),
        "focus": str(_state_value(state, "setup_focus", "")).strip(),
        "tech_stack": list(_state_value(state, "tech_stack", []) or []),
        "competencies": list(_state_value(state, "competencies", []) or []),
        "question_type": str(_state_value(state, "question_type", "auto")).strip(),
        "previous_questions": previous_questions[-3:],
        "question_index": int(_state_value(state, "current_question_index", 1) or 1),
        "question_plan": question_plan,
        "question_list_count": 1 if is_free_model(MODEL_NAME) else question_count,
        "should_abort": lambda: _question_generation_is_cancelled(state),
    }


def _build_question_meta(questions: list[dict[str, Any]] | None) -> dict[str, Any]:
    distribution = {key: 0 for key in ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")}
    prepared = [item for item in questions or [] if isinstance(item, dict)]
    for item in prepared:
        question_type = str(item.get("question_type", "")).strip()
        if question_type in distribution:
            distribution[question_type] += 1
    return {"total_questions": len(prepared), "distribution": distribution}


def _build_fallback_questions(payload: dict[str, Any]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    previous_questions = list(payload["previous_questions"])
    question_type = str(payload["question_type"])
    total_questions = int(payload.get("question_list_count") or 5)
    for index in range(1, total_questions + 1):
        question = generate_fallback_question(
            role=payload["role"],
            difficulty=payload["difficulty"],
            focus=payload["focus"],
            cv_context=payload["cv_context"],
            jd_context=payload["jd_context"],
            question_type=question_type,
            question_index=index,
            previous_questions=previous_questions,
            question_plan=payload["question_plan"],
        )
        previous_questions.append(question)
        questions.append(
            {
                "sequence_order": index,
                "question": question,
                "question_type": question_type,
                "focus_area": str(payload["question_plan"].get("focus_area", payload["focus"])).strip(),
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": payload["difficulty"],
                "what_interviewer_is_testing": [str(payload["question_plan"].get("purpose", "")).strip()] if str(payload["question_plan"].get("purpose", "")).strip() else [],
            }
        )
    return {"questions": questions, "meta": _build_question_meta(questions)}


def _generate_question(payload: dict[str, Any]) -> dict[str, Any]:
    clear_last_llm_call_metadata()
    try:
        bundle = get_next_question_for_session(
            role=payload["role"],
            difficulty=payload["difficulty"],
            persona=payload["persona"],
            response_style=payload["response_style"],
            focus=payload["focus"],
            cv_context=payload["cv_context"],
            question_index=payload["question_index"],
            jd_context=payload["jd_context"],
            asked_topics=payload["asked_topics"],
            tech_stack=payload["tech_stack"],
            competencies=payload["competencies"],
            question_type=payload["question_type"],
            previous_questions=payload["previous_questions"],
            temperature=payload["temperature"],
            gap_analysis=payload["gap_analysis"],
            question_list_count=int(payload.get("question_list_count") or 5),
            return_meta=True,
            should_abort=payload.get("should_abort"),
        )
    except Exception as exc:
        if "Free model limit reached" in str(exc):
            return {
                "token": payload["token"],
                "status": "rate_limited",
                "error": "Free model limit reached. Try later.",
                "questions": [],
                "meta": {},
                "llm_metadata": get_last_llm_call_metadata(),
            }
        LOGGER.exception("Question generation failed, using fallback bundle")
        bundle = _build_fallback_questions(payload)
    if isinstance(bundle, dict):
        questions = bundle.get("questions", [])
        meta = bundle.get("meta", _build_question_meta(questions if isinstance(questions, list) else []))
    elif isinstance(bundle, list):
        questions = bundle
        meta = _build_question_meta(bundle)
    elif isinstance(bundle, str):
        questions = [{"question": bundle}]
        meta = _build_question_meta(questions)
    else:
        fallback_bundle = _build_fallback_questions(payload)
        questions = fallback_bundle["questions"]
        meta = fallback_bundle["meta"]
    return {
        "token": payload["token"],
        "questions": questions,
        "meta": meta,
        "llm_metadata": get_last_llm_call_metadata(),
    }
def _finalise_question_job(
    state: Any,
    payload: dict[str, Any],
    questions: Any,
    status: str,
    error: str | None = None,
    notice: str = "",
    allow_current_question_update: bool = True,
    meta: dict[str, Any] | None = None,
    llm_metadata: dict[str, Any] | None = None,
) -> bool:
    _stop_question_generation(state)
    started_at = payload.get("started_at") or _state_value(state, QUESTION_GENERATION_STARTED_AT, None) or payload["question_plan"].get("started_at")
    prepared_questions = [item for item in questions if isinstance(item, dict)] if isinstance(questions, list) else ([{"question": questions.strip()}] if isinstance(questions, str) and questions.strip() else [])
    question_text = str(prepared_questions[0].get("question", "")).strip() if prepared_questions else (questions.strip() if isinstance(questions, str) else "")
    question_meta = meta or _build_question_meta(prepared_questions)
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
    state[QUESTION_GENERATION_FUTURE] = None
    state[QUESTION_GENERATION_STARTED_AT] = None
    state["generation_start_time"] = None
    state[QUESTION_GENERATION_READY] = True
    state[QUESTION_JOB_KEY] = {
        "status": status,
        "result": prepared_questions,
        "error": error,
        "started_at": started_at,
        "llm_metadata": llm_metadata,
    }
    LOGGER.info(
        "Question distribution: %s provider=%s model=%s task=%s",
        question_meta["distribution"],
        state["question_generation_provider"] or "unknown",
        state["question_generation_model"] or "unknown",
        state["question_generation_task"] or "unknown",
    )
    topic = extract_topic(state["current_question"])
    if topic:
        existing_topics = [str(item).strip().lower() for item in state.get("question_topics", [])]
        if topic not in existing_topics:
            state["question_topics"] = [*state.get("question_topics", []), topic][-8:]
    return True
def _recover_with_fallback(state: Any, payload: dict[str, Any], status: str, notice: str) -> bool:
    _stop_question_generation(state)
    fallback_bundle = _build_fallback_questions(payload)
    state["question_generation_notice"] = notice
    return _finalise_question_job(
        state,
        payload,
        fallback_bundle["questions"],
        status=status,
        error=notice,
        notice=notice,
        meta=fallback_bundle["meta"],
        llm_metadata={},
    )


def _log_root_cause(reason: str, payload: dict[str, Any], *, status: str, elapsed_seconds: float | None = None, error: str = "") -> None:
    elapsed_part = f"{elapsed_seconds:.2f}s" if elapsed_seconds is not None else "unknown"
    LOGGER.warning(
        "Question generation fallback root cause: reason=%s status=%s elapsed=%s role=%s difficulty=%s question_type=%s error=%s",
        reason,
        status,
        elapsed_part,
        payload["role"] or "unknown",
        payload["difficulty"] or "unknown",
        payload["question_type"] or "unknown",
        error or "none",
    )


def begin_question_generation(state: Any) -> None:
    payload = _build_payload(state)
    current_token = payload["token"] + 1
    payload["token"] = current_token
    state[QUESTION_GENERATION_CANCEL_EVENT] = Event()
    state[QUESTION_GENERATION_TOKEN] = current_token
    started_at = time()
    state[QUESTION_GENERATION_STARTED_AT] = started_at
    state["generation_start_time"] = started_at
    state[QUESTION_GENERATION_ERROR] = ""
    state[QUESTION_GENERATION_READY] = False
    state[QUESTION_GENERATION_NOTICE] = ""
    state["question_generation_model"] = ""
    state["question_generation_provider"] = ""
    state["question_generation_task"] = ""
    state[QUESTION_JOB_KEY] = _default_question_job(status=update_status("pending", "running"), started_at=started_at)
    state[QUESTION_GENERATION_FUTURE] = _EXECUTOR.submit(_generate_question, payload)
def reset_question_generation_state(state: Any) -> None:
    _stop_question_generation(state)
    state[QUESTION_GENERATION_FUTURE] = None
    state[QUESTION_GENERATION_STARTED_AT] = None
    state["generation_start_time"] = None
    state[QUESTION_GENERATION_ERROR] = ""
    state[QUESTION_GENERATION_READY] = False
    state[QUESTION_GENERATION_NOTICE] = ""
    state[QUESTION_JOB_KEY] = _default_question_job()
    state["question_meta"] = {}
    state["question_generation_model"] = ""
    state["question_generation_provider"] = ""
    state["question_generation_task"] = ""
def poll_question_generation(state: Any) -> bool:
    future = _state_value(state, QUESTION_GENERATION_FUTURE, None)
    job = _ensure_question_job(state)
    payload = _build_payload(state)
    start_time = _state_value(state, "generation_start_time", None) or job.get("started_at") or _state_value(state, QUESTION_GENERATION_STARTED_AT, None)

    if job.get("status") == "rate_limited":
        message = str(job.get("error") or "Free model limit reached. Try later.")
        state[QUESTION_GENERATION_ERROR] = message
        state[QUESTION_GENERATION_NOTICE] = message
        state["setup_error"] = message
        state["question_generation_future"] = None
        state[QUESTION_GENERATION_FUTURE] = None
        state[QUESTION_GENERATION_STARTED_AT] = None
        state["generation_start_time"] = None
        state[QUESTION_GENERATION_READY] = False
        state["is_loading"] = False
        state["current_screen"] = "setup"
        state[QUESTION_JOB_KEY] = job
        return True
    if job.get("status") in {"failed", "timeout"} and state.get("current_question"):
        return False
    if job.get("status") in {"failed", "timeout"} and not state.get("current_question"):
        _log_root_cause(
            "job_status",
            payload,
            status=str(job.get("status")),
            elapsed_seconds=(time() - float(start_time)) if start_time else None,
            error=str(job.get("error") or ""),
        )
        return _recover_with_fallback(
            state,
            payload,
            status=str(job.get("status")),
            notice=f"{BACKUP_NOTICE} The original question took longer than expected." if job.get("status") == "timeout" else f"{BACKUP_NOTICE} The original question could not be generated.",
        )

    if start_time and time() - float(start_time) > MAX_WAIT_SECONDS:
        elapsed_seconds = time() - float(start_time)
        job["status"] = update_status(job["status"], "timeout")
        state[QUESTION_JOB_KEY] = job
        _log_root_cause(
            "timeout_exceeded",
            payload,
            status="timeout",
            elapsed_seconds=elapsed_seconds,
            error=f"elapsed {elapsed_seconds:.2f}s exceeded wait limit {MAX_WAIT_SECONDS}s",
        )
        return _recover_with_fallback(
            state,
            payload,
            status="timeout",
            notice=f"{BACKUP_NOTICE} The original question took longer than expected.",
        )

    if not isinstance(future, Future):
        return False
    if not future.done():
        return False

    try:
        result = future.result()
    except Exception as exc:
        job["status"] = update_status(job["status"], "failed")
        job["error"] = str(exc)
        state[QUESTION_JOB_KEY] = job
        _log_root_cause(
            "future_exception",
            payload,
            status="failed",
            elapsed_seconds=(time() - float(start_time)) if start_time else None,
            error=str(exc),
        )
        return _recover_with_fallback(
            state,
            payload,
            status="failed",
            notice=f"{BACKUP_NOTICE} The original question could not be generated.",
        )

    if isinstance(result, dict) and result.get("status") == "rate_limited":
        job["status"] = "rate_limited"
        job["error"] = str(result.get("error") or "Free model limit reached. Try later.")
        state[QUESTION_JOB_KEY] = job
        return poll_question_generation(state)

    questions = result.get("questions", []) if isinstance(result, dict) else []
    if not questions:
        job["status"] = "failed"
        job["error"] = "Model unavailable"
        state[QUESTION_JOB_KEY] = job
        state[QUESTION_GENERATION_ERROR] = "Model unavailable"
        state[QUESTION_GENERATION_NOTICE] = "Model unavailable"
        state["setup_error"] = "Model unavailable"
        state["question_generation_future"] = None
        state[QUESTION_GENERATION_FUTURE] = None
        state[QUESTION_GENERATION_STARTED_AT] = None
        state["generation_start_time"] = None
        state[QUESTION_GENERATION_READY] = False
        state["is_loading"] = False
        state["launch_question_view"] = False
        state["has_active_session"] = False
        state["current_screen"] = "setup"
        return True

    if result.get("token") != int(_state_value(state, QUESTION_GENERATION_TOKEN, 0)):
        reset_question_generation_state(state)
        return False
    if job.get("status") == "timeout":
        return False

    job["status"] = update_status(job["status"], "completed")
    job["result"] = result.get("questions", [])
    job["error"] = None
    state[QUESTION_JOB_KEY] = job
    state[QUESTION_GENERATION_NOTICE] = ""
    state[QUESTION_GENERATION_ERROR] = ""
    return _finalise_question_job(
        state,
        payload,
        result.get("questions", []),
        status="completed",
        allow_current_question_update=job.get("status") != "timeout",
        meta=result.get("meta") if isinstance(result, dict) else None,
        llm_metadata=result.get("llm_metadata") if isinstance(result, dict) else None,
    )
