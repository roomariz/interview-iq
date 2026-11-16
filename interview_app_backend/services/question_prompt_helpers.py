"""Question generation prompt helpers."""

from __future__ import annotations

from interview_app_backend.services import question_service as service


def _build_strict_system_prompt(role: str, difficulty: str, persona: str, focus: str) -> str:
    return (
        "You are a senior technical interviewer.\n\n"
        "Generate ONE interview question based on the configuration.\n\n"
        "STRICT RULES:\n"
        "- The question MUST reflect the selected role, difficulty, persona, and focus.\n"
        "- The question MUST follow the priority order: role first, then CV if provided, then job description.\n"
        "- The question MUST be concrete, not abstract.\n"
        "- The question MUST include a realistic scenario.\n"
        "- The question MUST be answerable in 2–4 minutes (for Easy difficulty).\n"
        "- The question MUST test applied thinking, not theory.\n\n"
        f"ROLE: {role}\n"
        f"DIFFICULTY: {difficulty}\n"
        f"PERSONA: {persona}\n"
        f"FOCUS: {focus}\n\n"
        "QUESTION DESIGN RULES:\n"
        "- For Easy: Use simple, relatable scenarios (e.g. slow API, UI lag, basic DB query). Avoid system design or large-scale architecture.\n"
        "- For Performance Optimisation: Must include a performance issue (latency, slow load, inefficient query, etc.)\n"
        "- For Full Stack: Should involve frontend + backend OR API + DB interaction\n\n"
        "- Vary the scenario and focus area each time to avoid repetition.\n"
        "OUTPUT FORMAT:\n"
        "Return ONLY the question.\n"
        "No explanation.\n"
    )


def _build_few_shot_section(role: str, difficulty: str, focus: str) -> str:
    key = (role, difficulty, focus)
    examples = service.FEW_SHOT_EXAMPLES.get(key, [])

    if not examples:
        return ""

    section = "\nExamples:\n"
    for example in examples:
        section += f"Configuration: {example['Configuration']}\n"
        section += f"Question:\n{example['Question']}\n\n"
    return section


def _build_template_guidance(role: str, difficulty: str, focus: str) -> str:
    template = service._select_template(difficulty, focus)
    if template:
        return f"\nTemplate reference (use this structure):\n{template}\n"
    return ""


def _normalise_temperature(value: object | None) -> float:
    try:
        return float(value) if value is not None else 0.7
    except (TypeError, ValueError):
        return 0.7


def _question_prompt_style() -> str:
    return str(service.get_model_profile(service.MODEL_NAME).get("prompt_style", "strict"))


def _question_retry_limit() -> int:
    return service.get_retry_limit(service.MODEL_NAME)


def _question_strict_json(model_name: str | None = None) -> bool:
    profile = service.get_model_profile(model_name or service.MODEL_NAME)
    return bool(profile.get("strict_json", True))


def _build_question_plan(
    role: str,
    difficulty: str,
    question_index: int,
    cv_context: str,
    jd_context: str,
    asked_topics: list[str] | None,
    focus: str,
    question_type: str | None,
    previous_questions: list[str] | None = None,
) -> dict[str, object]:
    return service.build_question_prompt_context(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        previous_questions=previous_questions,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type or "auto",
    )

