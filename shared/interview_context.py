from collections.abc import Iterable


TECH_STACK_OPTIONS = [
    "Java / Spring Boot",
    "Python / FastAPI",
    "React / Angular",
    "Node.js / TypeScript",
    "SQL / PostgreSQL",
    "AWS / Docker",
    "Kubernetes / CI/CD",
]

COMPETENCY_OPTIONS = [
    "Performance optimisation",
    "System design",
    "Debugging",
    "API design",
    "Frontend architecture",
    "Ownership",
    "Communication",
    "Reliability",
    "Scalability",
    "Monitoring",
]

QUESTION_TYPE_OPTIONS = [
    "Auto",
    "Technical",
    "Behavioural",
    "System design",
    "Follow-up",
]

TECH_STACK_KEYWORDS = {
    "java": "Java / Spring Boot",
    "spring": "Java / Spring Boot",
    "fastapi": "Python / FastAPI",
    "python": "Python / FastAPI",
    "react": "React / Angular",
    "angular": "React / Angular",
    "node": "Node.js / TypeScript",
    "typescript": "Node.js / TypeScript",
    "postgres": "SQL / PostgreSQL",
    "sql": "SQL / PostgreSQL",
    "aws": "AWS / Docker",
    "docker": "AWS / Docker",
    "kubernetes": "Kubernetes / CI/CD",
    "ci/cd": "Kubernetes / CI/CD",
}

COMPETENCY_KEYWORDS = {
    "performance": "Performance optimisation",
    "latency": "Performance optimisation",
    "optimise": "Performance optimisation",
    "optimize": "Performance optimisation",
    "system design": "System design",
    "architecture": "System design",
    "debug": "Debugging",
    "bug": "Debugging",
    "api": "API design",
    "frontend": "Frontend architecture",
    "ui": "Frontend architecture",
    "ownership": "Ownership",
    "stakeholder": "Communication",
    "communication": "Communication",
    "reliab": "Reliability",
    "scale": "Scalability",
    "monitor": "Monitoring",
}


def _clean_text(value: str) -> str:
    return " ".join(str(value).split())


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = _clean_text(value)
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _match_keywords(text: str, mapping: dict[str, str]) -> list[str]:
    lowered = text.lower()
    return _dedupe(option for keyword, option in mapping.items() if keyword in lowered)


def infer_tech_stack_from_context(cv_context: str, jd_context: str) -> list[str]:
    return _match_keywords(f"{cv_context} {jd_context}", TECH_STACK_KEYWORDS)


def infer_competencies_from_context(role: str, cv_context: str, jd_context: str) -> list[str]:
    inferred = _match_keywords(f"{role} {cv_context} {jd_context}", COMPETENCY_KEYWORDS)
    if "behavioural" in role.lower():
        inferred = [*inferred, "Communication", "Ownership"]
    return _dedupe(inferred)


def normalise_question_type(question_type: str | None) -> str:
    value = _clean_text(question_type or "").lower().replace("-", "_")
    if not value or value == "auto":
        return "auto"
    if value in {"system design", "system_design"}:
        return "system_design"
    if value in {"follow up", "follow_up"}:
        return "follow_up"
    if value in {"behavioural", "behavioral"}:
        return "behavioural"
    if value == "technical":
        return "technical"
    return "auto"


def resolve_question_type(
    question_type: str | None,
    competencies: Iterable[str],
    cv_context: str,
    jd_context: str,
) -> str:
    explicit = normalise_question_type(question_type)
    if explicit != "auto":
        return explicit

    competency_blob = " ".join(competencies).lower()
    context_blob = f"{cv_context} {jd_context}".lower()
    if any(token in competency_blob for token in ("system design", "scalability", "reliability")):
        return "system_design"
    if any(token in competency_blob for token in ("ownership", "communication")):
        return "behavioural"
    if "follow up" in context_blob:
        return "follow_up"
    return "technical"
