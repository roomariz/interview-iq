"""Question generation quality."""

from __future__ import annotations

from interview_app_backend.services import question_service as service
from interview_app_backend.services.question_validation import has_unsupported_technology


def _soft_validate_question(question: str, role: str, cv_context: str, jd_context: str) -> bool:
    question_lower = question.lower()
    role_keywords = service._extract_role_keywords(role)
    cv_keywords = service._extract_context_keywords(cv_context)
    jd_keywords = service._extract_context_keywords(jd_context)
    if role_keywords and not any(keyword in question_lower for keyword in role_keywords):
        return False
    if cv_context.strip() and cv_keywords and not any(keyword in question_lower for keyword in cv_keywords):
        return False
    if jd_context.strip() and jd_keywords and not any(keyword in question_lower for keyword in jd_keywords):
        return False
    return True


def is_valid_question(question: str) -> bool:
    if not isinstance(question, str) or len(question.strip()) < 20:
        return False
    if "?" not in question:
        return False
    return True


def _is_generic_question(question_lower: str) -> bool:
    return any(
        phrase in question_lower
        for phrase in (
            "how would you apply your experience",
            "how would you apply your relevant experience",
            "based on your experience",
            "your relevant experience",
            "explain your approach",
            "what would you do in general",
            "tell me about yourself",
            "describe yourself",
        )
    )


def validate_question(question: str, focus: str, question_type: str = "technical") -> tuple[bool, str]:
    if not question.strip():
        return False, "empty"

    question_lower = question.lower()

    if focus.lower() == "performance":
        has_performance_keyword = any(kw in question_lower for kw in service.PERFORMANCE_KEYWORDS)
        if not has_performance_keyword:
            return False, "missing_performance_keyword"

    if service._is_generic_question(question_lower):
        return False, "abstract_question"

    if question_type == "behavioural":
        behavioural_indicators = ["tell me about", "describe a time", "walk me through", "give an example"]
        if not any(indicator in question_lower for indicator in behavioural_indicators):
            return False, "no_behavioural_scenario"
        return True, "valid"

    if question_type in {"system_design", "deep_dive"}:
        design_indicators = ["design", "architect", "scalable", "reliability", "trade-off", "load"]
        if not any(indicator in question_lower for indicator in design_indicators):
            return False, "no_system_design_scenario"
        return True, "valid"

    scenario_indicators = [
        "your application", "your api", "a page", "a user", "a colleague", "the system", "endpoint",
        "your data", "your database", "your pipeline", "your server", "your code", "your query",
    ]
    extended_scenario = (
        any(subject in question_lower for subject in ("production", "release", "deployment", "stakeholder", "team", "service", "workflow"))
        and any(problem in question_lower for problem in ("incident", "regression", "fail", "slow", "conflict", "disagree", "change", "constraint", "cannot", "outage"))
    )
    if not extended_scenario and not any(indicator in question_lower for indicator in scenario_indicators):
        return False, "no_scenario"

    return True, "valid"


def _passes_generation_checks(question: str, role: str, difficulty: str, focus: str, question_type: str) -> bool:
    return service._soft_validate_question(question, role, focus, difficulty)


def _matches_context(question: str, cv_context: str, jd_context: str) -> bool:
    question_text = question.lower()
    context_tokens = service._topic_tokens(cv_context) + service._topic_tokens(jd_context)
    generic_terms = {"system", "experience", "work", "role", "question"}
    context_hits = [token for token in context_tokens if token not in generic_terms and token in question_text]
    return bool(context_hits)


def _topic_relevance(question: str, cv_context: str, jd_context: str, question_type: str = "behavioural", focus: str = "") -> bool:
    question_lower = question.lower()
    focus_lower = (focus or "").lower()

    performance_terms = [
        "slow", "latency", "load time", "response time", "performance",
        "optimise", "optimize", "query", "api", "database", "frontend", "backend",
    ]

    if "performance" in focus_lower:
        if any(term in question_lower for term in performance_terms):
            return True

    combined_context = f"{cv_context} {jd_context}".strip().lower()
    if not combined_context:
        return True

    if question_type in ("cv_based", "jd_based", "gap_targeted"):
        context_tokens = set(service._topic_tokens(cv_context) + service._topic_tokens(jd_context))
        if not context_tokens:
            return True

        if service._matches_context(question, cv_context, jd_context):
            return True

        topic = service.extract_topic(question)
        if not topic:
            return False
        topic_tokens = set(topic.split())
        if topic_tokens & context_tokens:
            return True
        return False

    return True


def _validate_single_question(
    question: str,
    *,
    role: str,
    cv_context: str,
    jd_context: str,
    focus: str,
    question_type: str,
) -> tuple[bool, str]:
    if not service.is_valid_question(question):
        return False, "invalid_question"
    is_valid, reason = service.validate_question(question, focus, question_type)
    if not is_valid:
        return False, reason
    context_mode = service._context_mode(cv_context, jd_context)
    supported_terms = service._contextual_supported_terms(context_mode, role, cv_context, jd_context)
    if not service._topic_relevance(question, cv_context, jd_context, question_type, focus):
        return False, "ungrounded_question"
    if not service._soft_validate_question(question, role, cv_context, jd_context):
        return False, "missing_context_grounding"
    if (has_unsupported_technology(question, f"{role} {cv_context} {jd_context}")
            or service._has_hallucinated_tech(question, supported_terms)):
        return False, "hallucinated_tech"
    return True, "valid"

