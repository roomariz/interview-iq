"""Question generation context."""

from __future__ import annotations

from interview_app_backend.services import question_service as service


def _build_context_block(role: str, cv_context: str, jd_context: str) -> str:
    return (
        f"Role: {role}\n"
        f"Candidate CV context: {cv_context.strip()}\n"
        f"Job Description context: {jd_context.strip()}\n"
    )


def _select_template(difficulty: str, focus: str) -> str:
    if focus.lower() == "performance":
        templates = service.PERFORMANCE_TEMPLATES.get(difficulty, service.PERFORMANCE_TEMPLATES["Easy"])
        return service.random.choice(templates)
    return None


def _select_question_type(cv_context: str, jd_context: str, asked_topics: list[str], question_index: int = 1) -> str:
    if cv_context.strip():
        return "technical"
    if jd_context.strip():
        return "technical"
    if asked_topics and len(asked_topics) >= 2:
        return "follow_up"
    return "technical"


def _format_template(template: str, role: str, difficulty: str, cv_context: str, jd_context: str) -> str:
    replacements = {
        "{duration}": service.random.choice(["5 seconds", "several seconds", "a few seconds"]),
        "{baseline}": service.random.choice(["200ms", "100ms", "150ms"]),
        "{degraded}": service.random.choice(["800ms", "1 second", "600ms"]),
        "{scenario}": service.random.choice(["a performance issue", "an API slowdown", "a loading problem"]),
        "{cv_skill}": service._extract_skill_from_context(cv_context) or "your relevant experience",
        "{jd_requirement}": service._extract_skill_from_context(jd_context) or "the required skill",
        "{gap}": "performance optimisation",
        "{strength}": "technical implementation",
        "{situation}": "you had to optimise something that was running slowly",
        "{action}": "improved the performance of a slow system",
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _extract_skill_from_context(context: str) -> str | None:
    if not context.strip():
        return None
    keywords = ["react", "python", "javascript", "sql", "api", "database", "frontend", "backend", "node", "django", "spring", "spring boot"]
    context_lower = context.lower()
    for keyword in keywords:
        if keyword in context_lower:
            return keyword
    return None


def _extract_role_keywords(role: str) -> list[str]:
    role_lower = role.lower()
    for key, keywords in service.ROLE_KEYWORDS.items():
        if key in role_lower:
            return keywords[:3]
    if "platform" in role_lower or "infrastructure" in role_lower:
        return ["platform", "infrastructure"]
    if "qa" in role_lower or "test" in role_lower:
        return ["test", "regression"]
    return [role_lower] if role_lower else []


def _extract_context_keywords(context: str) -> list[str]:
    keywords = [
        "python",
        "java",
        "spring",
        "typescript",
        "javascript",
        "react",
        "angular",
        "fastapi",
        "django",
        "sql",
        "postgres",
        "api",
        "rest",
        "microservices",
        "database",
        "performance",
        "testing",
        "aws",
        "docker",
        "kubernetes",
        "monitoring",
        "scalability",
        "reliability",
        "communication",
        "leadership",
        "caching",
    ]
    lowered = context.lower()
    return [keyword for keyword in keywords if keyword in lowered][:3]


def _normalise_scenario_type(value: object, question_type: str = "") -> str:
    scenario_type = str(value or "").strip().lower().replace("-", "_")
    if scenario_type in service.ALLOWED_SCENARIO_TYPES:
        return scenario_type
    question_type_key = str(question_type or "").strip().lower().replace("-", "_")
    return service.QUESTION_TYPE_TO_SCENARIO_TYPE.get(question_type_key, "debugging")

