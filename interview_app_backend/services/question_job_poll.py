"""Question generation job poll."""
from __future__ import annotations

from interview_app_backend.services import question_generation_job as _job_api


def poll_question_generation(state: _job_api.Any) -> bool:
    future = _job_api._state_value(state, _job_api.QUESTION_GENERATION_FUTURE, None)
    job = _job_api._ensure_question_job(state)
    payload = _job_api._build_payload(state)
    start_time = _job_api._state_value(state, "generation_start_time", None) or job.get("started_at") or _job_api._state_value(state, _job_api.QUESTION_GENERATION_STARTED_AT, None)

    if job.get("status") == "rate_limited":
        message = str(job.get("error") or "Free model limit reached. Try later.")
        state[_job_api.QUESTION_GENERATION_ERROR] = message
        state[_job_api.QUESTION_GENERATION_NOTICE] = message
        state["setup_error"] = message
        state["question_generation_future"] = None
        state[_job_api.QUESTION_GENERATION_FUTURE] = None
        state[_job_api.QUESTION_GENERATION_STARTED_AT] = None
        state["generation_start_time"] = None
        state[_job_api.QUESTION_GENERATION_READY] = False
        state["is_loading"] = False
        state["current_screen"] = "setup"
        state[_job_api.QUESTION_JOB_KEY] = job
        return True
    if job.get("status") in {"failed", "timeout"} and state.get("current_question"):
        return False
    if job.get("status") in {"failed", "timeout"} and not state.get("current_question"):
        _job_api._log_root_cause(
            "job_status",
            payload,
            status=str(job.get("status")),
            elapsed_seconds=(_job_api.time() - float(start_time)) if start_time else None,
            error=str(job.get("error") or ""),
        )
        return _job_api._recover_with_fallback(
            state,
            payload,
            status=str(job.get("status")),
            notice=f"{_job_api.BACKUP_NOTICE} The original question took longer than expected." if job.get("status") == "timeout" else f"{_job_api.BACKUP_NOTICE} The original question could not be generated.",
        )

    if start_time and _job_api.time() - float(start_time) > _job_api.MAX_WAIT_SECONDS:
        elapsed_seconds = _job_api.time() - float(start_time)
        job["status"] = _job_api.update_status(job["status"], "timeout")
        state[_job_api.QUESTION_JOB_KEY] = job
        _job_api._log_root_cause(
            "timeout_exceeded",
            payload,
            status="timeout",
            elapsed_seconds=elapsed_seconds,
            error=f"elapsed {elapsed_seconds:.2f}s exceeded wait limit {_job_api.MAX_WAIT_SECONDS}s",
        )
        return _job_api._recover_with_fallback(
            state,
            payload,
            status="timeout",
            notice=f"{_job_api.BACKUP_NOTICE} The original question took longer than expected.",
        )

    if not isinstance(future, _job_api.Future):
        return False
    if not future.done():
        return False

    try:
        result = future.result()
    except Exception as exc:
        job["status"] = _job_api.update_status(job["status"], "failed")
        job["error"] = str(exc)
        state[_job_api.QUESTION_JOB_KEY] = job
        _job_api._log_root_cause(
            "future_exception",
            payload,
            status="failed",
            elapsed_seconds=(_job_api.time() - float(start_time)) if start_time else None,
            error=str(exc),
        )
        return _job_api._recover_with_fallback(
            state,
            payload,
            status="failed",
            notice=f"{_job_api.BACKUP_NOTICE} The original question could not be generated.",
        )

    if isinstance(result, dict) and result.get("status") == "rate_limited":
        job["status"] = "rate_limited"
        job["error"] = str(result.get("error") or "Free model limit reached. Try later.")
        state[_job_api.QUESTION_JOB_KEY] = job
        return _job_api.poll_question_generation(state)

    questions = result.get("questions", []) if isinstance(result, dict) else []
    if not questions:
        job["status"] = "failed"
        job["error"] = "Model unavailable"
        state[_job_api.QUESTION_JOB_KEY] = job
        state[_job_api.QUESTION_GENERATION_ERROR] = "Model unavailable"
        state[_job_api.QUESTION_GENERATION_NOTICE] = "Model unavailable"
        state["setup_error"] = "Model unavailable"
        state["question_generation_future"] = None
        state[_job_api.QUESTION_GENERATION_FUTURE] = None
        state[_job_api.QUESTION_GENERATION_STARTED_AT] = None
        state["generation_start_time"] = None
        state[_job_api.QUESTION_GENERATION_READY] = False
        state["is_loading"] = False
        state["launch_question_view"] = False
        state["has_active_session"] = False
        state["current_screen"] = "setup"
        return True

    if result.get("token") != int(_job_api._state_value(state, _job_api.QUESTION_GENERATION_TOKEN, 0)):
        _job_api.reset_question_generation_state(state)
        return False
    if job.get("status") == "timeout":
        return False

    job["status"] = _job_api.update_status(job["status"], "completed")
    job["result"] = result.get("questions", [])
    job["error"] = None
    state[_job_api.QUESTION_JOB_KEY] = job
    state[_job_api.QUESTION_GENERATION_NOTICE] = ""
    state[_job_api.QUESTION_GENERATION_ERROR] = ""
    return _job_api._finalise_question_job(
        state,
        payload,
        result.get("questions", []),
        status="completed",
        allow_current_question_update=job.get("status") != "timeout",
        meta=result.get("meta") if isinstance(result, dict) else None,
        llm_metadata=result.get("llm_metadata") if isinstance(result, dict) else None,
    )

