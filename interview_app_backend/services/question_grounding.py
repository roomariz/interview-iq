"""Question generation grounding."""

from __future__ import annotations

from interview_app_backend.services import question_service as service
from interview_app_backend.services.question_validation import has_unsupported_technology


def _supported_terms_for_context(role: str, cv_context: str, jd_context: str) -> set[str]:
    context = service.resolve_missing_context(role, cv_context, jd_context)
    terms = set(context["role_keywords"]) | set(context["cv_keywords"]) | set(context["jd_keywords"])
    role_lower = " ".join(str(role).split()).lower()
    terms.add(role_lower)

    active_groups: set[str] = set()
    for term in terms:
        lowered = term.lower()
        group = service.TERM_TO_GROUP.get(lowered)
        if group:
            active_groups.add(group)
    for group_name, synonyms in service.ROLE_BASELINE_GROUPS.items():
        if group_name in role_lower:
            active_groups.update(synonyms)

    allowed_terms: set[str] = set()
    for group in active_groups:
        allowed_terms.update(service.SEMANTIC_TECH_GROUPS.get(group, set()))
    allowed_terms.update(terms)
    return {term for term in allowed_terms if term}


def _expand_semantic_terms(base_terms: set[str]) -> set[str]:
    expanded = set(base_terms)
    active_groups: set[str] = set()
    for term in base_terms:
        group = service.TERM_TO_GROUP.get(term)
        if group:
            active_groups.add(group)
    for group in active_groups:
        expanded.update(service.SEMANTIC_TECH_GROUPS.get(group, set()))
    return expanded


def _contextual_supported_terms(mode: str, role: str, cv_context: str, jd_context: str) -> set[str]:
    context = service.resolve_missing_context(role, cv_context, jd_context)
    base_terms = set(service.ROLE_ONLY_GROUNDING_TERMS) | set(context["role_keywords"])
    if mode in {"jd_only", "cv_jd"}:
        base_terms.update(context["jd_keywords"])
    if mode in {"cv_only", "cv_jd"}:
        base_terms.update(context["cv_keywords"])
    return service._expand_semantic_terms(base_terms)


def _context_mode(cv_context: str, jd_context: str) -> str:
    has_cv = bool(" ".join(str(cv_context).split()).strip())
    has_jd = bool(" ".join(str(jd_context).split()).strip())
    if has_cv and has_jd:
        return "cv_jd"
    if has_jd:
        return "jd_only"
    if has_cv:
        return "cv_only"
    return "role_only"


def _source_terms(item: dict[str, object]) -> tuple[list[str], list[str]]:
    source_basis = item.get("source_basis") if isinstance(item.get("source_basis"), dict) else {}
    cv_terms = [str(term).strip().lower() for term in list(source_basis.get("cv_terms_used", []) or []) if str(term).strip()]
    jd_terms = [str(term).strip().lower() for term in list(source_basis.get("jd_terms_used", []) or []) if str(term).strip()]
    return cv_terms, jd_terms


def _classify_dimension(item: dict[str, object]) -> str:
    scenario_type = service._normalise_scenario_type(item.get("scenario_type"), str(item.get("question_type", "")))
    return service.DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery")


def _has_allowed_term(question: str, allowed_terms: set[str]) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in allowed_terms)


def _bundle_dimensions(questions: list[dict[str, object]]) -> list[str]:
    return [service._classify_dimension(question) for question in questions if isinstance(question, dict)]


def _has_supported_grounding(question: str, supported_terms: set[str]) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in supported_terms)


def _has_hallucinated_tech(question: str, supported_terms: set[str]) -> bool:
    # Generic capabilities (monitoring, leadership, reliability) are not named tools.
    # Word boundaries also prevent React/REST/API matching reaction/restore/capital.
    # Callers additionally check raw context so semantic expansion cannot authorise a tool.
    return has_unsupported_technology(question, " ".join(supported_terms))

