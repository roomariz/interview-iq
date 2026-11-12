from collections.abc import Iterable

from interview_app_backend.llm.prompts.question_guardrails import build_question_guardrails_block

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


def _summarise_text(text: str, fallback: str) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return fallback
    return cleaned[:220]


def build_candidate_profile(cv_context: str, jd_context: str) -> str:
    return (
        f"CV summary: {_summarise_text(cv_context, 'No CV provided')}\n"
        f"JD summary: {_summarise_text(jd_context, 'No job description provided')}"
    )
def _format_list(values: Iterable[str], fallback: str) -> str:
    items = _dedupe(values)
    return ", ".join(items) if items else fallback
def _avoid_topics_line(asked_topics: Iterable[str] | None) -> str:
    topics = _dedupe(asked_topics or [])
    if not topics:
        return ""
    return "Avoid repeating these topics: " + ", ".join(topics) + "\n"
def _question_requirements(question_type: str) -> str:
    if question_type == "behavioural":
        return (
            "- Generate a realistic behavioural question\n"
            "- Use a STAR-style scenario\n"
            "- Require ownership, communication, or collaboration reasoning\n"
            "- Include a real-world challenge and constraints\n"
        )
    if question_type == "system_design":
        return (
            "- Generate a realistic system design question\n"
            "- Include scale, reliability, data flow, or trade-offs\n"
            "- Require architectural reasoning and decisions\n"
            "- Avoid high-level theory without a concrete scenario\n"
        )
    if question_type == "follow_up":
        return (
            "- Generate a realistic follow-up question\n"
            "- Deepen the previous answer with a concrete constraint or trade-off\n"
            "- Require the candidate to explain decisions in more detail\n"
        )
    return (
        "- Generate one realistic, scenario-based interview question\n"
        "- Follow the priority order: ROLE first, then CV if provided, then JOB DESCRIPTION\n"
        "- If CV is provided, personalise using candidate experience; if JD is provided, align with role expectations and required skills; if both are provided, prioritise overlap or probe gaps\n"
        "- Avoid generic or theoretical questions\n"
        "- Include a real-world situation with constraints and trade-offs\n"
        "- Require reasoning and decision-making, not just definition recall\n"
    )
def build_question_generation_prompt(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    jd_context: str = "",
    tech_stack: Iterable[str] | None = None,
    competencies: Iterable[str] | None = None,
    question_type: str | None = None,
    focus: str = "General",
    asked_topics: Iterable[str] | None = None,
    previous_questions: Iterable[str] | None = None,
    focus_area: str | None = None,
) -> str:
    explicit_tech_stack = _dedupe(tech_stack or [])
    resolved_tech_stack = explicit_tech_stack or infer_tech_stack_from_context(cv_context, jd_context)
    explicit_competencies = _dedupe(competencies or [])
    resolved_competencies = explicit_competencies or infer_competencies_from_context(role, cv_context, jd_context)
    resolved_question_type = resolve_question_type(question_type, resolved_competencies, cv_context, jd_context)
    focus_label = _clean_text(focus) or (resolved_competencies[0] if resolved_competencies else "General")

    return (
        "You are a senior technical interviewer.\n\n"
        "PRIORITY_ORDER:\n"
        "- ROLE (highest priority)\n"
        "- CV if provided\n"
        "- JOB DESCRIPTION if provided\n\n"
        f"ROLE: {role}\n"
        "TECH_STACK:\n"
        f"{_format_list(resolved_tech_stack, 'Infer from CV and job description')}\n\n"
        "CANDIDATE_PROFILE:\n"
        f"{build_candidate_profile(cv_context, jd_context)}\n\n"
        "TARGET_COMPETENCIES:\n"
        f"{_format_list(resolved_competencies, 'Infer from role and context')}\n\n"
        "QUESTION_TYPE:\n"
        f"{resolved_question_type}\n\n"
        "QUESTION_PLAN:\n"
        f"Type: {resolved_question_type}\n"
        f"Purpose: {('Probe ownership, communication, and collaboration' if resolved_question_type == 'behavioural' else 'Probe architectural judgement and trade-offs' if resolved_question_type == 'system_design' else 'Deepen the previous answer with a realistic constraint' if resolved_question_type == 'follow_up' else 'Test role fit using the selected plan')}\n"
        f"Focus: {focus_label}\n"
        f"Focus area: {focus_area or focus_label}\n"
        f"Variation rule: Do not generate similar or overlapping questions.\n"
        f"Previous question count: {len(_dedupe(previous_questions or []))}\n\n"
        f"PERSONA: {persona}\n"
        f"Response style: {response_style}\n"
        f"DIFFICULTY: {difficulty}\n\n"
        f"{_avoid_topics_line(asked_topics)}"
        f"PREVIOUS_QUESTIONS: {', '.join(_dedupe(previous_questions or [])[:3]) or 'None'}\n\n"
        "QUESTION_REQUIREMENTS:\n"
        f"{_question_requirements(resolved_question_type)}"
        "- Vary the scenario and focus area each time to avoid repetition\n"
        "- The question must NOT assume a specific programming language unless it is explicitly provided in TECH_STACK.\n"
        "- It must remain tightly aligned to the candidate profile, role, and difficulty.\n\n"
        f"{build_question_guardrails_block(resolved_question_type)}\n"
        "OUTPUT_FORMAT:\n"
        "Return ONLY one question.\n"
    )
