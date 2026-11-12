from __future__ import annotations

from collections.abc import Iterable, Mapping

FOCUS_AREA_SEQUENCE = ["core", "experience", "jd_alignment", "gap", "deep_dive"]
FOCUS_AREA_LABELS = {
    "core": "core responsibilities",
    "experience": "candidate experience",
    "jd_alignment": "job description alignment",
    "gap": "identified gaps",
    "deep_dive": "trade-offs, constraints, and decision-making",
}

QUESTION_SEQUENCE = [
    {"type": "role_based", "purpose": "Check role fit and practical baseline", "focus_area": "core", "focus_label": FOCUS_AREA_LABELS["core"], "difficulty_shift": 0.0},
    {"type": "cv_based", "purpose": "Probe candidate experience from the CV", "focus_area": "experience", "focus_label": FOCUS_AREA_LABELS["experience"], "difficulty_shift": 0.0},
    {"type": "jd_based", "purpose": "Align with job description expectations", "focus_area": "jd_alignment", "focus_label": FOCUS_AREA_LABELS["jd_alignment"], "difficulty_shift": 0.1},
    {"type": "gap_targeted", "purpose": "Test weak or missing areas", "focus_area": "gap", "focus_label": FOCUS_AREA_LABELS["gap"], "difficulty_shift": 0.1},
    {"type": "deep_dive", "purpose": "Test trade-offs and senior reasoning", "focus_area": "deep_dive", "focus_label": FOCUS_AREA_LABELS["deep_dive"], "difficulty_shift": 0.2},
]

ROLE_KEYWORDS = {
    "backend": ["api", "service", "database"],
    "frontend": ["user interface", "browser", "state"],
    "full stack": ["frontend", "backend", "api"],
    "data": ["pipeline", "dataset", "query"],
    "devops": ["deployment", "monitoring", "infrastructure"],
    "platform": ["reliability", "scale", "service"],
    "qa": ["test", "regression", "release"],
    "product": ["stakeholders", "trade-offs", "requirements"],
}

KNOWN_CONTEXT_KEYWORDS = (
    "python", "java", "spring", "typescript", "javascript", "react", "angular", "fastapi", "django", "node", "sql",
    "postgres", "api", "database", "performance", "testing", "aws", "docker", "kubernetes", "monitoring",
    "scalability", "reliability", "leadership", "communication",
)


def _clean(value: object) -> str:
    return " ".join(str(value).split())


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = _clean(value).lower()
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _state_value(state: object, key: str, default: object = "") -> object:
    if isinstance(state, Mapping):
        return state.get(key, default)
    return getattr(state, key, default)


def _keywords_from_text(text: str, fallback: list[str] | None = None) -> list[str]:
    lowered = _clean(text).lower()
    found = [keyword for keyword in KNOWN_CONTEXT_KEYWORDS if keyword in lowered]
    return _dedupe(found or (fallback or []))[:3]


def resolve_missing_context(role: str, cv_context: str, jd_context: str) -> dict[str, list[str]]:
    role_lower = role.lower()
    role_keywords = next((keywords for key, keywords in ROLE_KEYWORDS.items() if key in role_lower), [role_lower] if role_lower else [])
    return {
        "role_keywords": _dedupe(role_keywords or [role_lower])[:3],
        "cv_keywords": _keywords_from_text(cv_context),
        "jd_keywords": _keywords_from_text(jd_context),
    }


def _resolve_type(question_type: str, cv_context: str, jd_context: str) -> str:
    has_cv = bool(_clean(cv_context))
    has_jd = bool(_clean(jd_context))
    resolved = _clean(question_type).lower().replace("-", "_") or "auto"
    if resolved != "auto":
        return resolved
    if has_cv and has_jd:
        return "cv_based"
    if has_cv:
        return "cv_based"
    if has_jd:
        return "jd_based"
    return "role_based"


def _resolve_sequence_index(question_index: int) -> int:
    return min(max(question_index, 1) - 1, len(QUESTION_SEQUENCE) - 1)


def _resolve_previous_questions(previous_questions: Iterable[str] | None) -> list[str]:
    return _dedupe(previous_questions or [])[:3]


def build_question_prompt_context(
    role: str,
    difficulty: str,
    question_index: int,
    cv_context: str = "",
    jd_context: str = "",
    previous_questions: Iterable[str] | None = None,
    asked_topics: Iterable[str] | None = None,
    focus: str = "",
    question_type: str = "auto",
) -> dict[str, object]:
    sequence_item = QUESTION_SEQUENCE[_resolve_sequence_index(question_index)]
    context = resolve_missing_context(role, cv_context, jd_context)
    resolved_type = _resolve_type(question_type, cv_context, jd_context)
    if resolved_type == "cv_based" and not context["cv_keywords"] and context["jd_keywords"]:
        resolved_type = "jd_based"
    if resolved_type == "jd_based" and not context["jd_keywords"] and context["cv_keywords"]:
        resolved_type = "cv_based"
    if resolved_type in {"cv_based", "jd_based"} and not (context["cv_keywords"] or context["jd_keywords"]):
        resolved_type = "role_based"
    if resolved_type == "role_based" and sequence_item["type"] != "role_based" and question_index > 1:
        resolved_type = sequence_item["type"]
    return {
        "role": _clean(role),
        "difficulty": _clean(difficulty),
        "question_index": question_index,
        "question_type": resolved_type,
        "purpose": sequence_item["purpose"],
        "focus": _clean(focus) or sequence_item["focus_label"],
        "focus_area": sequence_item["focus_area"],
        "focus_label": sequence_item["focus_label"],
        "difficulty_shift": sequence_item["difficulty_shift"],
        "previous_questions": _resolve_previous_questions(previous_questions),
        "asked_topics": _dedupe(asked_topics or []),
        "cv_context": _clean(cv_context),
        "jd_context": _clean(jd_context),
        **context,
    }


def select_question_plan(session_state: object) -> dict[str, object]:
    question_index = int(_state_value(session_state, "current_question_index", 1) or 1)
    role = str(_state_value(session_state, "role", "") or _state_value(session_state, "setup_role", "")).strip()
    difficulty = str(_state_value(session_state, "difficulty", "") or _state_value(session_state, "setup_difficulty", "")).strip()
    cv_context = str(_state_value(session_state, "setup_cv_content", "") or _state_value(session_state, "cv_context", "")).strip()
    jd_context = str(_state_value(session_state, "setup_job_description", "") or _state_value(session_state, "jd_context", "")).strip()
    answers = _state_value(session_state, "answers", []) or []
    previous_questions = []
    for answer in answers:
        if isinstance(answer, Mapping):
            previous_questions.append(str(answer.get("question", "")).strip())
    return build_question_prompt_context(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        previous_questions=previous_questions,
        asked_topics=_state_value(session_state, "question_topics", []) or [],
        focus=str(_state_value(session_state, "setup_focus", "")).strip(),
        question_type=str(_state_value(session_state, "question_type", "auto")).strip(),
    )
