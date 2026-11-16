"""Question generation fallback templates."""

from __future__ import annotations

from interview_app_backend.services import question_service as service


def _build_fallback_detail(question_plan: dict[str, object]) -> str:
    question_type = str(question_plan.get("question_type", "role_based"))
    role_keywords = list(question_plan.get("role_keywords", []) or [])
    cv_keywords = list(question_plan.get("cv_keywords", []) or [])
    jd_keywords = list(question_plan.get("jd_keywords", []) or [])
    focus_area = str(question_plan.get("focus_area", "")).strip()
    focus_label = str(question_plan.get("focus_label", "")).strip() or focus_area.replace("_", " ")
    if question_type == "cv_based":
        return cv_keywords[0] if cv_keywords else focus_label or "the experience highlighted in your CV"
    if question_type == "jd_based":
        return jd_keywords[0] if jd_keywords else focus_label or "the requirement in the job description"
    if question_type == "gap_targeted":
        return (jd_keywords[0] if jd_keywords else "") or (cv_keywords[0] if cv_keywords else "") or focus_label or "the weakest area"
    if question_type == "deep_dive":
        return " and ".join([item for item in [role_keywords[0] if role_keywords else "", jd_keywords[0] if jd_keywords else "", focus_label] if item]) or "the trade-off"
    return role_keywords[0] if role_keywords else focus_label or "the role"


def _pick_template(values: list[str], question_index: int, previous_questions: list[str] | None) -> str:
    offset = len(previous_questions or [])
    return values[offset % len(values)]


def generate_safe_fallback(
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str = "",
    jd_context: str = "",
    question_type: str = "behavioural",
    question_index: int = 1,
    previous_questions: list[str] | None = None,
    question_plan: dict[str, object] | None = None,
) -> str:
    if not cv_context.strip() and not jd_context.strip():
        # These are explicit backup scenarios, not claims about a candidate's history.
        templates = {
            "cv_based": [
                "Your application has a regression after a release in your {role} team. What evidence would you gather to isolate the cause and recover safely?",
                "A colleague reports that the system produces incorrect results after a change in your {role} project. How would you reproduce and debug the problem?",
            ],
            "jd_based": [
                "A user reports that your application is slow during busy periods in your {role} work. How would you measure the bottleneck and improve performance safely?",
                "Response time in the system doubles under load for your {role} team. Which measurements would you compare before choosing a performance improvement?",
            ],
            "behavioural": [
                "Tell me about a time your {role} team disagreed about delivery priorities. How did you resolve the conflict and communicate the outcome?",
                "Describe a time when you had to coordinate stakeholders during an incident in your {role} work. How did you manage expectations?",
            ],
            "deep_dive": [
                "Stakeholders ask your {role} team to design the system for a growing workload. Which trade-offs would guide the design and protect reliability?",
                "A new requirement changes the design of your application in your {role} project. How would you compare architectural options and their trade-offs?",
            ],
            "gap_targeted": [
                "Demand for the system is growing beyond the capacity of your {role} team. How would you scale the workflow while protecting delivery?",
                "Requests arriving in your pipeline exceed what your {role} team can handle. How would you prioritise capacity changes and check that scaling works?",
            ],
        }
        selected_type = "jd_based" if focus.lower() == "performance" else question_type
        values = templates.get(selected_type)
        if values:
            template = values[((question_index - 1) // 5) % len(values)]
            keywords = service._extract_role_keywords(role)
            role_label = role.lower()
            if keywords and not any(keyword in role_label for keyword in keywords):
                role_label += f" ({keywords[0]})"
            return template.format(role=role_label)

    plan = question_plan or service.build_question_prompt_context(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        previous_questions=previous_questions,
        focus=focus,
        question_type=question_type,
    )
    role_lower = str(plan.get("role", role)).lower().strip() or "the team"
    question_type = str(plan.get("question_type", question_type))
    detail = service._build_fallback_detail(plan)
    cv_hint = list(plan.get("cv_keywords", []) or [])
    jd_hint = list(plan.get("jd_keywords", []) or [])
    role_hint = list(plan.get("role_keywords", []) or [])
    role_focus = role_hint[0] if role_hint else (role_lower.split()[0] if role_lower else "application")
    previous = list(previous_questions or [])
    template = next(
        (value for key, value in service.ROLE_FALLBACK_TEMPLATES.items() if key in role_lower),
        "You are working on a {role} team where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    )
    if focus.lower() == "performance":
        detail = detail if detail != "the role" else "performance"
        if difficulty.lower() == "easy":
            return f"A user reports that a page in your application takes several seconds to load. How would you investigate {detail} and improve performance without causing regressions?"
        return f"Your application is experiencing performance issues under load. How would you investigate {detail}, identify the bottleneck, and improve performance safely?"
    if question_type == "cv_based" and cv_context.strip():
        scenario = f"a realistic issue in a {role_lower} project"
        if jd_hint:
            scenario = f"{scenario} that also touches {jd_hint[0]}"
        template = service._pick_template(service.QUESTION_TYPE_TEMPLATES["cv_based"], question_index, previous)
        return template.format(cv_skill=detail, scenario=scenario, role_focus=role_focus, role=role_lower)
    if question_type == "jd_based" and jd_context.strip():
        scenario = f"a release issue for a {role_lower} team"
        if cv_hint:
            scenario = f"{scenario} building on {cv_hint[0]}"
        template = service._pick_template(service.QUESTION_TYPE_TEMPLATES["jd_based"], question_index, previous)
        return template.format(jd_requirement=detail, scenario=scenario, role_focus=role_focus, role=role_lower)
    if question_type == "gap_targeted":
        template = service._pick_template(service.QUESTION_TYPE_TEMPLATES["gap_targeted"], question_index, previous)
        return template.format(strength=f"your {role_lower} experience", gap=detail, role_focus=role_focus, role=role_lower)
    if question_type == "deep_dive":
        question = template.format(role=role_lower, detail=detail)
        return question.replace("How would you investigate the issue, decide on a fix, and keep the release stable?", "How would you weigh the trade-offs, make the decision, and keep the release stable?")
    return template.format(role=role_lower, detail=detail)


def generate_fallback_question(
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str = "",
    jd_context: str = "",
    question_type: str = "behavioural",
    question_index: int = 1,
    previous_questions: list[str] | None = None,
    question_plan: dict[str, object] | None = None,
) -> str:
    return service.generate_safe_fallback(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        question_index=question_index,
        previous_questions=previous_questions,
        question_plan=question_plan,
    )

