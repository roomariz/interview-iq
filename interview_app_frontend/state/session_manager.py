import streamlit as st

from interview_app_backend.llm.prompts.question_generation import infer_competencies_from_context
from interview_app_backend.llm.prompts.question_generation import infer_tech_stack_from_context
from interview_app_backend.llm.prompts.question_generation import resolve_question_type
from interview_app_backend.services.gap_analysis_service import analyse_gaps
from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_backend.services.evaluation_service import generate_example_answer
from config.model_profiles import get_question_count
from config.model_profiles import is_free_model
from config.settings import MODEL_NAME
from interview_app_backend.services.question_generation_job import begin_question_generation
from interview_app_backend.services.question_generation_job import reset_question_generation_state
from interview_app_frontend.state.answer_evaluation_job import begin_answer_evaluation
from interview_app_frontend.state.answer_evaluation_job import consume_answer_evaluation
from interview_app_frontend.state.answer_evaluation_job import reset_answer_evaluation_state
from interview_app_frontend.state.state_schema import DEFAULT_SESSION_STATE
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import build_follow_up, build_key_takeaway
from interview_app_frontend.utils.session_summary_view import build_session_summary_view
from interview_app_frontend.utils.request_log import log_request

MIN_ANSWER_LENGTH = 50
MAX_ANSWER_LENGTH = 2000
DEFAULT_QUESTION = (
    "Describe a time you improved system performance under constraints. "
    "Include the challenge, your approach, and measurable results."
)
SECURITY_WARNING = (
    "This application supports interview preparation only. "
    "Please provide a relevant interview response."
)
SETUP_VALIDATION_ERROR = "Please complete the required setup fields before starting the interview."
SETUP_REQUIRED_FIELDS = ("setup_role", "setup_persona", "setup_difficulty")
ADAPTATION_SIGNAL_THRESHOLD = 2
COMPETENCY_BY_FOCUS = {
    "Relevance": "Question relevance",
    "Structure": "Structure",
    "Specificity": "Measurable outcomes",
    "Communication": "Communication",
    "Problem-Solving Approach": "Trade-offs and reasoning",
}
FOCUS_TO_QUESTION_TYPE = {
    "Question relevance": "technical",
    "Structure": "technical",
    "Measurable outcomes": "technical",
    "Communication": "behavioural",
    "Trade-offs and reasoning": "system_design",
}
PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore instructions",
    "override system",
    "system prompt",
    "prompt injection",
)


def _setup_value(key: str, fallback: str) -> str:
    value = str(st.session_state.get(key, "")).strip()
    return value or fallback


def _coerce_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _derive_focus_areas(scores: dict[str, object]) -> list[str]:
    weak_scores = []
    for dimension, label in COMPETENCY_BY_FOCUS.items():
        try:
            score = int(scores.get(dimension.lower(), scores.get(dimension, 0)))
        except (TypeError, ValueError):
            score = 0
        if score <= 4:
            weak_scores.append(label)
    return _dedupe(weak_scores)


def _question_type_from_focus_areas(focus_areas: list[str], default: str = "auto") -> str:
    for focus in focus_areas:
        question_type = FOCUS_TO_QUESTION_TYPE.get(focus)
        if question_type:
            return question_type
    return default


def _merge_competencies(base: list[str], focus_areas: list[str], streak: int) -> list[str]:
    merged = _dedupe([*focus_areas, *base])
    if streak >= ADAPTATION_SIGNAL_THRESHOLD and focus_areas:
        merged = _dedupe([*focus_areas, *merged])
    return merged[:8]


def _update_adaptation_state(state, scores: dict[str, object], base_competencies: list[str]) -> None:
    focus_areas = _derive_focus_areas(scores)
    prior_log = list(state.get("adaptation_log", []))
    primary_focus = focus_areas[0] if focus_areas else ""
    streak = 1
    if prior_log and isinstance(prior_log[-1], dict) and prior_log[-1].get("focus") == primary_focus:
        try:
            streak = int(prior_log[-1].get("streak", 1)) + 1
        except (TypeError, ValueError):
            streak = 2
    if primary_focus:
        prior_log.append({"focus": primary_focus, "streak": streak})
    state.adaptation_log = prior_log[-6:]
    state.focus_areas = focus_areas[:4]
    state.competencies = _merge_competencies(base_competencies, focus_areas, streak)
    if streak >= ADAPTATION_SIGNAL_THRESHOLD and primary_focus:
        state.question_type = _question_type_from_focus_areas([primary_focus], state.get("question_type", "auto"))


def validate_answer(answer: str) -> str:
    text = answer.strip()
    if not text:
        return "Please enter an answer before submitting."
    if len(text) < MIN_ANSWER_LENGTH:
        return f"Answer must be at least {MIN_ANSWER_LENGTH} characters to provide meaningful feedback."
    if len(text) > MAX_ANSWER_LENGTH:
        return "Answer limited to 2,000 characters. Try to be concise."

    lowered = text.lower()
    if any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS):
        return SECURITY_WARNING

    return ""


def ensure_session_state() -> None:
    for key, value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


def update_answer(value: str) -> None:
    st.session_state.answer = value


def clear_answer() -> None:
    st.session_state.answer = ""
    st.session_state.answer_submit_error = ""


def _is_valid_evaluation_for_storage(feedback: dict) -> bool:
    scores = feedback.get("scores")
    required_dims = frozenset(("relevance", "structure", "specificity", "communication", "problem_solving_approach"))
    if scores is None or not isinstance(scores, dict):
        return False
    return required_dims.issubset(scores.keys())


def _apply_answer_feedback(state, question: str, answer: str, feedback: dict) -> None:
    import time as time_module

    if not _is_valid_evaluation_for_storage(feedback):
        state.answer_evaluation_notice = "Could not store this evaluation due to incomplete scores."
        return

    view_model = normalise_feedback_payload(feedback)
    trust = feedback.get("trust", {})
    evaluation_confidence = feedback.get("evaluation_confidence", {})
    state.answers = [
        *state.get("answers", []),
        {
            "question": question,
            "answer": answer,
            "scores": dict(view_model.get("scores", {})),
            "labels": dict(view_model.get("labels", {})) if isinstance(view_model.get("labels"), dict) else {},
            "overall_decision": str(view_model.get("overall_decision", "")).strip(),
            "summary": str(view_model.get("feedback", {}).get("summary", "")).strip() if isinstance(view_model.get("feedback"), dict) else "",
            "strengths": list(view_model.get("strengths", [])) if isinstance(view_model.get("strengths"), list) else [],
            "key_issues": list(view_model.get("key_issues", [])) if isinstance(view_model.get("key_issues"), list) else [],
            "improvements": list(view_model.get("improvements", [])) if isinstance(view_model.get("improvements"), list) else [],
            "trust": dict(trust) if isinstance(trust, dict) else {},
            "evaluation_confidence": dict(evaluation_confidence) if isinstance(evaluation_confidence, dict) else {},
        },
    ]
    state.reference_answer = feedback.get("reference_answer", "")
    state.semantic_similarity_score = feedback.get("semantic_similarity_score", 0.0)
    state.feedback = feedback
    follow_up = build_follow_up(view_model)
    takeaway = build_key_takeaway(view_model)
    _update_adaptation_state(state, view_model.get("scores", {}), _coerce_list(state.get("competencies", [])))
    memory_entry = {
        "question": view_model["question"],
        "takeaway": takeaway,
        "follow_up_question": follow_up.get("question", ""),
        "follow_up_stage": follow_up.get("stage", 1),
        "focus": follow_up.get("target_dimension", "problem_solving_approach"),
    }
    state.follow_up_questions = [*state.get("follow_up_questions", []), follow_up]
    relevance_score = int(view_model.get("scores", {}).get("relevance", 0))
    memory_allowed = bool(view_model.get("memory_storage_allowed", True)) and relevance_score >= 3
    if memory_allowed:
        state.future_session_memory = [*state.get("future_session_memory", []), memory_entry][-5:]
    if state.get("session_start_time"):
        state.session_duration_minutes = int((time_module.time() - state.session_start_time) / 60)
    state.current_screen = "feedback"
    state.session_complete = False
    state.is_loading = False
    state.answer_evaluation_error = ""
    state.answer_evaluation_notice = ""
    reset_answer_evaluation_state(state)


def finalise_answer_submission(question: str, answer: str, feedback: dict) -> None:
    _apply_answer_feedback(st.session_state, question, answer, feedback)


def submit_answer() -> None:
    state = st.session_state
    answer = state.get("answer", "").strip()
    error = validate_answer(answer)
    if error:
        state.answer_submit_error = error
        return

    state.answer_submit_error = ""
    question = state.get("current_question") or DEFAULT_QUESTION
    try:
        begin_answer_evaluation(state, question, answer, evaluate_submission)
    except Exception:
        state.answer_submit_error = "We could not start evaluating your answer right now. Please try again in a few moments."
        return

    feedback = consume_answer_evaluation(state, timeout=0.2)
    if isinstance(feedback, dict) and not feedback.get("error"):
        _apply_answer_feedback(state, question, answer, feedback)
        return
    if isinstance(feedback, dict) and feedback.get("error"):
        state.answer_submit_error = "We could not evaluate your answer right now. Please try again in a few moments."
        state.current_screen = "question"
        state.is_loading = False
        return

    state.current_screen = "evaluating_answer"
    state.is_loading = True
    state.answer_evaluation_error = ""


def show_sample_answer() -> None:
    state = st.session_state
    feedback = state.get("feedback") if isinstance(state.get("feedback"), dict) else {}
    source_answer = str(state.get("answer") or feedback.get("answer", "")).strip()
    question = str(state.get("current_question") or feedback.get("question", DEFAULT_QUESTION)).strip()
    if is_free_model(MODEL_NAME):
        sample_answer = "Example answers are unavailable in free mode."
    elif source_answer:
        try:
            sample_answer = generate_example_answer(source_answer)
        except Exception:
            sample_answer = source_answer
    else:
        sample_answer = "No submitted answer is available to rewrite."

    state.sample_answer = sample_answer.strip()
    state.sample_answer_question = question or DEFAULT_QUESTION
    state.sample_answer_source_answer = source_answer
    state.current_screen = "sample_answer"


def return_to_feedback() -> None:
    st.session_state.current_screen = "feedback"


def go_to_session_summary() -> None:
    state = st.session_state
    state.summary = build_session_summary_view(state)
    state.current_screen = "summary"
    state.launch_question_view = False
    st.session_state.session_complete = True


def return_to_question() -> None:
    state = st.session_state
    state.current_screen = "question"
    state.has_active_session = True
    state.launch_question_view = False
    state.session_complete = False
    state.answer = ""
    state.answer_submit_error = ""


def advance_to_next_question() -> None:
    state = st.session_state
    current_index = int(state.get("current_question_index") or 0)
    next_index = current_index + 1
    total_questions = int(state.get("session_question_limit") or get_question_count(MODEL_NAME) or 3)
    if next_index > total_questions:
        state.current_screen = "summary"
        state.session_complete = True
        state.launch_question_view = False
        return
    state.current_question_index = next_index
    state.current_screen = "generating_question"
    state.launch_question_view = False
    state.has_active_session = True
    state.session_complete = False
    state.answer = ""
    state.answer_submit_error = ""
    state.current_question = ""
    state.prepared_questions = []
    state.base_questions = []
    state.follow_up_questions = []
    state.question_generation_error = ""
    state.question_generation_notice = ""
    state.question_generation_ready = False
    state.question_generation_future = None
    state.question_job = {"status": "pending", "result": None, "error": None, "started_at": None}


def set_screen(name: str) -> None:
    st.session_state.current_screen = name


def start_interview() -> None:
    import time as time_module

    state = st.session_state
    if not is_setup_valid():
        state.setup_error = SETUP_VALIDATION_ERROR
        return

    state.has_active_session = True
    state.session_complete = False
    state.current_question_index = 1
    state.session_start_time = time_module.time()
    state.session_question_limit = get_question_count(MODEL_NAME)
    state.is_loading = True
    state.current_screen = "generating_question"
    state.launch_question_view = False
    state.answer = ""
    state.answer_submit_error = ""
    state.reference_answer = ""
    state.semantic_similarity_score = 0.0
    state.sample_answer = ""
    state.sample_answer_question = ""
    state.sample_answer_source_answer = ""
    state.answers = []
    state.feedback = []
    state.summary = {}
    state.question_topics = []
    state.adaptation_log = []
    state.prepared_questions = []
    state.base_questions = []
    state.follow_up_questions = []
    state.role = _setup_value("setup_role", "Backend Engineer")
    state.difficulty = _setup_value("setup_difficulty", "Medium")
    state.persona = _setup_value("setup_persona", "Strict")
    state.response_style = _setup_value("setup_response_style", "Detailed")
    state.temperature = _setup_value("setup_temperature", "0.7")
    job_description = _setup_value("setup_job_description", "")
    cv_content = _setup_value("setup_cv_content", "")
    state.setup_job_description = job_description
    state.setup_cv_content = cv_content
    detected_tech_stack = infer_tech_stack_from_context(cv_content, job_description)
    selected_tech_stack = _coerce_list(state.get("setup_tech_stack", state.get("setup_tech_stack_selection", [])))
    state.detected_tech_stack = detected_tech_stack
    state.setup_tech_stack = selected_tech_stack or detected_tech_stack
    state.tech_stack = state.setup_tech_stack
    inferred_competencies = infer_competencies_from_context(state.role, cv_content, job_description)
    state.competencies = inferred_competencies
    state.focus_areas = []
    state.question_type = resolve_question_type(
        state.get("question_type", "auto"),
        state.competencies,
        cv_content,
        job_description,
    )
    state.gap_analysis = analyse_gaps(cv_content, job_description)
    state.job_description = "Added" if job_description else "—"
    state.cv_status = "Uploaded" if cv_content else "—"
    state.current_question = ""
    state.question_generation_error = ""
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)
    begin_question_generation(state)
    log_request(
        task="question_generation",
        provider="open-router",
        model=state.get("question_generation_model", ""),
        status="pending",
    )
    state.setup_error = ""


def is_setup_valid() -> bool:
    state = st.session_state
    return all(str(state.get(key, "")).strip() for key in SETUP_REQUIRED_FIELDS)


def get_setup_validation_state() -> dict[str, bool]:
    state = st.session_state
    return {key: bool(str(state.get(key, "")).strip()) for key in SETUP_REQUIRED_FIELDS}


def restart_session() -> None:
    state = st.session_state
    memory = state.get("future_session_memory", [])
    for key, value in DEFAULT_SESSION_STATE.items():
        state[key] = value
    state.future_session_memory = memory
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)


def exit_session() -> None:
    state = st.session_state
    memory = state.get("future_session_memory", [])
    for key, value in DEFAULT_SESSION_STATE.items():
        state[key] = value
    state.future_session_memory = memory
    state.current_screen = "welcome"  # Reset state but keep relevant data if needed
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)


def return_to_setup() -> None:
    state = st.session_state
    state.current_screen = "setup"
    state.launch_question_view = False
    state.has_active_session = False
    state.session_complete = False
    state.current_question_index = 0
    state.current_question = ""
    state.answer = ""
    state.answer_submit_error = ""
    state.reference_answer = ""
    state.semantic_similarity_score = 0.0
    state.sample_answer = ""
    state.sample_answer_question = ""
    state.sample_answer_source_answer = ""
    state.answers = []
    state.feedback = []
    state.summary = {}
    state.is_loading = False
    state.prepared_questions = []
    state.base_questions = []
    state.follow_up_questions = []
    state.gap_analysis = {}
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)
