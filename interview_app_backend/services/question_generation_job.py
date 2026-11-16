"""Question job interface; workers receive snapshots, UI updates stay on the main thread."""
from __future__ import annotations
from __future__ import annotations  # noqa: F401
import logging  # noqa: F401
from concurrent.futures import Future, ThreadPoolExecutor  # noqa: F401
from time import time  # noqa: F401
from threading import Event  # noqa: F401
from typing import Any  # noqa: F401
from interview_app_backend.services.question_service import extract_topic  # noqa: F401
from interview_app_backend.services.question_service import generate_fallback_question  # noqa: F401
from interview_app_backend.services.question_service import get_next_question_for_session  # noqa: F401
from interview_app_backend.services.question_sequence import select_question_plan  # noqa: F401
from config.model_profiles import get_question_count  # noqa: F401
from config.model_profiles import is_free_model  # noqa: F401
from interview_app_backend.llm.client import clear_last_llm_call_metadata  # noqa: F401
from interview_app_backend.llm.client import get_last_llm_call_metadata  # noqa: F401
from config.settings import MODEL_NAME  # noqa: F401
from interview_app_backend.services.question_job_payload import (  # noqa: F401
    _state_value,
    _default_question_job,
    _ensure_question_job,
    _question_generation_is_cancelled,
    _stop_question_generation,
    _build_payload,
    _build_question_meta,
    _build_fallback_questions,
)
from interview_app_backend.services.question_job_worker import (  # noqa: F401
    _generate_question,
)
from interview_app_backend.services.question_job_result import (  # noqa: F401
    _finalise_question_job,
    _recover_with_fallback,
    _log_root_cause,
)
from interview_app_backend.services.question_job_poll import (  # noqa: F401
    poll_question_generation,
)

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

_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="question-generation")

def update_status(current: str, new: str) -> str:
    assert new in VALID_TRANSITIONS[current]
    return new

def begin_question_generation(state: Any) -> None:
    _stop_question_generation(state)
    state[QUESTION_GENERATION_CANCEL_EVENT] = Event()
    payload = _build_payload(state)
    current_token = payload["token"] + 1
    payload["token"] = current_token
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
    state[QUESTION_GENERATION_FUTURE] = _EXECUTOR.submit(_generate_question, payload, get_next_question_for_session)

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
