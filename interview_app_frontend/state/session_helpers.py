import streamlit as st

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


def _is_valid_evaluation_for_storage(feedback: dict) -> bool:
    scores = feedback.get("scores")
    required_dims = frozenset(("relevance", "structure", "specificity", "communication", "problem_solving_approach"))
    if scores is None or not isinstance(scores, dict):
        return False
    return required_dims.issubset(scores.keys())
