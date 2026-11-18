"""Frontend jobs own snapshots and futures; the backend owns question generation."""

from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from time import time

from interview_app_frontend.services.api_client import BackendError, InterviewAPIClient

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="question-http")


def reset_question_generation_state(state):
    future = state.get("question_generation_future")
    if isinstance(future, Future):
        future.cancel()
    state["question_generation_token"] = int(state.get("question_generation_token", 0)) + 1
    for key in ("question_generation_future", "question_generation_started_at", "generation_start_time"):
        state[key] = None
    for key in ("question_generation_error", "question_generation_notice", "question_generation_model",
                "question_generation_provider", "question_generation_task"):
        state[key] = ""
    state["question_generation_ready"] = False
    state["question_job"] = {"status": "pending", "result": None, "error": None, "started_at": None}
    state["question_meta"] = {}


def begin_question_generation(state):
    if isinstance(state.get("question_generation_future"), Future):
        return
    reset_question_generation_state(state)
    client = InterviewAPIClient()  # Resolve server-side Streamlit secrets before starting a worker.
    payload = {key: state.get(key, default) for key, default in {
        "role": "Backend Engineer", "difficulty": "Medium", "persona": "Neutral",
        "response_style": "Detailed", "temperature": 0.7, "gap_analysis": {},
        "tech_stack": [], "competencies": [], "question_type": "auto",
    }.items()}
    payload.update(
        cv_context=state.get("setup_cv_content", ""), jd_context=state.get("setup_job_description", ""),
        asked_topics=state.get("question_topics", []), focus=state.get("setup_focus", ""),
        previous_questions=[entry["question"] for entry in state.get("answers", [])
                            if isinstance(entry, dict) and entry.get("question")][-3:],
        question_index=int(state.get("current_question_index", 1) or 1),
        question_list_count=int(state.get("backend_question_list_count", 1)),
    )
    try:
        payload["temperature"] = float(payload["temperature"])
    except (TypeError, ValueError):
        payload["temperature"] = 0.7
    started = time()
    state["generation_start_time"] = started
    state["question_generation_started_at"] = started
    state["question_job"] = {"status": "running", "result": None, "error": None, "started_at": started}
    state["question_generation_future"] = _EXECUTOR.submit(client.question, **deepcopy(payload))


def poll_question_generation(state):
    future = state.get("question_generation_future")
    if not isinstance(future, Future) or not future.done():
        return False
    state["question_generation_future"] = None
    try:
        result = future.result()
        questions = result.get("questions", [])
        if not questions or any(not isinstance(item, dict) or not str(item.get("question", "")).strip()
                                for item in questions):
            raise BackendError("The interview service returned an incomplete questionnaire.")
    except Exception as exc:
        message = str(exc) if isinstance(exc, BackendError) else "Model unavailable. Please try again."
        state["question_job"] = {"status": "failed", "result": [], "error": message, "started_at": None}
        for key in ("question_generation_error", "question_generation_notice", "setup_error"):
            state[key] = message
        for key in ("is_loading", "launch_question_view", "question_generation_ready"):
            state[key] = False
        state["current_screen"] = "generating_question"
        return True
    state["prepared_questions"] = questions
    state["base_questions"] = list(questions)
    state["current_question"] = questions[0]["question"]
    # Preserve the topic history used to avoid repeating later questions.
    from shared.question_topics import extract_topic
    topic = extract_topic(state["current_question"])
    if topic and topic not in state.get("question_topics", []):
        state["question_topics"] = [*state.get("question_topics", []), topic][-8:]
    state["question_meta"] = result["meta"]
    for name in ("model", "provider", "task"):
        state[f"question_generation_{name}"] = result.get("llm_metadata", {}).get(name, "")
    state["question_job"] = {"status": "completed", "result": questions, "error": None, "started_at": None}
    state["current_screen"] = "question"
    state["is_loading"] = False
    state["launch_question_view"] = True
    state["has_active_session"] = True
    state["question_generation_ready"] = True
    state["question_generation_notice"] = ""
    state["question_generation_error"] = ""
    return True
