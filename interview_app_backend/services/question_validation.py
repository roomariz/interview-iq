"""Quality checks shared by model output and existing fallback candidates."""

import re

from interview_app_backend.llm.question_contract import QuestionValidationError

NAMED_TECHNOLOGIES = {
    "python", "java", "javascript", "typescript", "react", "angular", "node", "sql",
    "postgres", "postgresql", "mysql", "aws", "docker", "kubernetes", "redis", "kafka",
    "rabbitmq", "graphql", "fastapi", "django", "spring",
}


def unsupported_technologies(question: str, context: str) -> list[str]:
    def mentions(term, text):
        return bool(re.search(r"\b" + re.escape(term) + r"\b", text.lower()))

    return sorted(term for term in NAMED_TECHNOLOGIES if mentions(term, question) and not mentions(term, context))


def has_unsupported_technology(question: str, context: str) -> bool:
    return bool(unsupported_technologies(question, context))


def validate_generated_items(items, *, count, role, cv_context, jd_context, previous_questions=None):
    from interview_app_backend.services import question_service as service

    if len(items) != count:
        raise QuestionValidationError(f"invalid_question_count: expected {count}, received {len(items)}")
    for index, item in enumerate(items, start=1):
        terms = unsupported_technologies(service._question_text(item), f"{role} {cv_context} {jd_context}")
        if terms:
            reason = "scenario_a_contains_tech" if not cv_context.strip() and not jd_context.strip() else "hallucinated_tech"
            raise QuestionValidationError(f"question[{index}]: {reason}: unsupported technology: {', '.join(terms)}. "
                                          "Use only technologies explicitly supplied in the role, CV or job description.")
    valid, reason = service._validate_question_bundle(
        items, role=role, cv_context=cv_context, jd_context=jd_context, expected_count=count,
    )
    if not valid:
        raise QuestionValidationError(reason)
    for index, item in enumerate(items, start=1):
        question = service._question_text(item)
        scenario = item.get("scenario_type")
        valid, reason = service._validate_single_question(
            question, role=role, cv_context=cv_context, jd_context=jd_context,
            focus="performance" if scenario == "performance" else "",
            question_type="system_design" if scenario == "system_design" else "behavioural" if scenario == "behavioural" else "technical",
        )
        if not valid:
            raise QuestionValidationError(f"question[{index}]: {reason}. "
                                          "Keep the scenario classification; describe a concrete situation, problem and task. "
                                          "For performance, describe a slowdown or capacity constraint; do not add unrelated tools.")
        if service._is_similar_to_previous(question, previous_questions):
            raise QuestionValidationError(f"question[{index}]: duplicate_previous_question")
    if count > 1:
        try:
            unique = service.deduplicate_questions(items)
        except service.DuplicateQuestionError as exc:
            raise QuestionValidationError("duplicate_question: fewer than five distinct questions") from exc
        if len(unique) != count:
            raise QuestionValidationError("duplicate_question: repeated scenario or opening pattern")
