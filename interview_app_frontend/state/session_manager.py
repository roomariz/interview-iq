from interview_app_frontend.state.session_helpers import (  # noqa: F401
    _setup_value, _coerce_list, _dedupe, _derive_focus_areas, _question_type_from_focus_areas, _merge_competencies, _update_adaptation_state, validate_answer, _is_valid_evaluation_for_storage,
    DEFAULT_QUESTION, SETUP_VALIDATION_ERROR, SETUP_REQUIRED_FIELDS, MIN_ANSWER_LENGTH, MAX_ANSWER_LENGTH, SECURITY_WARNING,
)
from interview_app_frontend.state.session_feedback import _apply_answer_feedback
from interview_app_frontend.state.session_navigation import (  # noqa: F401
    update_answer, clear_answer, return_to_feedback, go_to_session_summary, return_to_question, advance_to_next_question, set_screen, restart_session, exit_session, return_to_setup,
)
import streamlit as st

from interview_app_frontend.services.api_client import InterviewAPIClient, BackendError
from interview_app_frontend.services.api_client import evaluate_submission, generate_example_answer
from interview_app_frontend.services.settings import is_free_model, MODEL_NAME
from interview_app_frontend.state.question_generation_job import begin_question_generation
from interview_app_frontend.state.question_generation_job import reset_question_generation_state
from interview_app_frontend.state.answer_evaluation_job import begin_answer_evaluation
from interview_app_frontend.state.answer_evaluation_job import consume_answer_evaluation
from interview_app_frontend.state.answer_evaluation_job import reset_answer_evaluation_state
from interview_app_frontend.state.state_schema import DEFAULT_SESSION_STATE
from interview_app_frontend.utils.request_log import log_request

def ensure_session_state() -> None:
    from copy import deepcopy

    for key, value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)

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
    if state.get("backend_free_mode", is_free_model(MODEL_NAME)):
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

def start_interview() -> None:
    import time as time_module

    state = st.session_state
    if not is_setup_valid():
        state.setup_error = SETUP_VALIDATION_ERROR
        return

    try:
        context = InterviewAPIClient().context(
            role=_setup_value("setup_role", "Backend Engineer"),
            cv_context=_setup_value("setup_cv_content", ""),
            jd_context=_setup_value("setup_job_description", ""),
            question_type=state.get("question_type", "auto"),
        )
    except (BackendError, ValueError):
        state.setup_error = "Could not prepare the interview. Check your inputs and backend connection, then try again."
        return
    state.backend_free_mode = context["free_mode"]
    state.backend_question_list_count = context["question_list_count"]
    state.backend_model = context["model"]
    state.backend_provider = context["provider"]

    state.has_active_session = True
    state.session_complete = False
    state.current_question_index = 1
    state.session_start_time = time_module.time()
    state.session_question_limit = context["session_question_limit"]
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
    detected_tech_stack = context["tech_stack"]
    selected_tech_stack = _coerce_list(state.get("setup_tech_stack", state.get("setup_tech_stack_selection", [])))
    state.detected_tech_stack = detected_tech_stack
    state.setup_tech_stack = selected_tech_stack or detected_tech_stack
    state.tech_stack = state.setup_tech_stack
    inferred_competencies = context["competencies"]
    state.competencies = inferred_competencies
    state.focus_areas = []
    state.question_type = context["question_type"]
    state.gap_analysis = context["gap_analysis"]
    state.job_description = "Added" if job_description else "—"
    state.cv_status = "Uploaded" if cv_content else "—"
    state.current_question = ""
    state.question_generation_error = ""
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)
    begin_question_generation(state)
    log_request(
        task="question_generation",
        provider=context["provider"],
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
