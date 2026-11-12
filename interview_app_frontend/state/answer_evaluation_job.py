from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from time import time
from typing import Any, Callable

from config.settings import MODEL_NAME
from interview_app_frontend.utils.request_log import log_request
from interview_app_frontend.utils.request_log import update_pending_request


ANSWER_EVALUATION_FUTURE = "answer_evaluation_future"
ANSWER_EVALUATION_STARTED_AT = "answer_evaluation_started_at"
ANSWER_EVALUATION_ERROR = "answer_evaluation_error"
ANSWER_EVALUATION_NOTICE = "answer_evaluation_notice"

LOGGER = logging.getLogger(__name__)
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="answer-evaluation")


def reset_answer_evaluation_state(state: Any) -> None:
    state[ANSWER_EVALUATION_FUTURE] = None
    state[ANSWER_EVALUATION_STARTED_AT] = None
    state[ANSWER_EVALUATION_ERROR] = ""
    state[ANSWER_EVALUATION_NOTICE] = ""


def begin_answer_evaluation(state: Any, question: str, answer: str, evaluator: Callable[[str, str], dict[str, Any]]) -> None:
    reset_answer_evaluation_state(state)
    state[ANSWER_EVALUATION_STARTED_AT] = time()
    state[ANSWER_EVALUATION_NOTICE] = "Evaluating your answer now. We are checking relevance, evidence, and scoring."
    state[ANSWER_EVALUATION_FUTURE] = _EXECUTOR.submit(evaluator, question, answer)
    log_request(
        task="answer_evaluation",
        provider="open-router",
        model=MODEL_NAME,
        status="running",
    )


def consume_answer_evaluation(state: Any, timeout: float = 0.0) -> dict[str, Any] | None:
    future = state.get(ANSWER_EVALUATION_FUTURE)
    if not isinstance(future, Future):
        return None
    try:
        result = future.result(timeout=timeout)
    except FutureTimeoutError:
        return None
    except Exception as exc:
        LOGGER.exception("Answer evaluation failed")
        started_at = float(state.get(ANSWER_EVALUATION_STARTED_AT) or time())
        state[ANSWER_EVALUATION_ERROR] = str(exc)
        state[ANSWER_EVALUATION_FUTURE] = None
        state[ANSWER_EVALUATION_NOTICE] = ""
        update_pending_request(
            task="answer_evaluation",
            status="failed",
            error=str(exc),
            provider="open-router",
            model=MODEL_NAME,
            latency_ms=int((time() - started_at) * 1000),
        )
        return {"error": str(exc)}

    started_at = float(state.get(ANSWER_EVALUATION_STARTED_AT) or time())
    state[ANSWER_EVALUATION_FUTURE] = None
    state[ANSWER_EVALUATION_NOTICE] = ""
    if isinstance(result, dict) and result.get("error"):
        update_pending_request(
            task="answer_evaluation",
            status="failed",
            error=str(result.get("error", "")),
            provider="open-router",
            model=MODEL_NAME,
            latency_ms=int((time() - started_at) * 1000),
        )
        return result

    update_pending_request(
        task="answer_evaluation",
        status="completed",
        provider="open-router",
        model=MODEL_NAME,
        latency_ms=int((time() - started_at) * 1000),
    )
    return result if isinstance(result, dict) else {}
