"""Question generation bundle."""

from __future__ import annotations

from interview_app_backend.services import question_service as service
from interview_app_backend.services.question_validation import has_unsupported_technology


def _question_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("question", "")).strip()
    return str(item).strip()


def _question_item(question: str, payload: dict[str, object]) -> dict[str, object]:
    scenario_type = service._normalise_scenario_type(payload.get("scenario_type"), str(payload.get("question_type", "")))
    return {
        "question": question,
        "question_type": str(payload.get("question_type", "cv_based")).strip() or "cv_based",
        "scenario_type": scenario_type,
        "dimension": service.DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery"),
        "focus_area": str(payload.get("focus_area", payload.get("focus", ""))).strip(),
        "source_basis": {
            "cv_terms_used": list(payload.get("cv_keywords", []) or []),
            "jd_terms_used": list(payload.get("jd_keywords", []) or []),
            "gap_used": payload.get("gap_used"),
        },
        "difficulty_level": str(payload.get("difficulty", "")).strip(),
        "what_interviewer_is_testing": list(payload["what_interviewer_is_testing"]) if isinstance(payload.get("what_interviewer_is_testing"), list) else ([str(payload.get("purpose", "")).strip()] if str(payload.get("purpose", "")).strip() else []),
    }


def _filter_question_items(
    items: list[dict[str, object]],
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    required_count: int,
) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in items:
        question = service._question_text(item)
        if not service.is_valid_question(question):
            continue
        lowered = question.lower()
        if lowered in seen or service._is_similar_to_previous(question, previous_questions):
            continue
        item_type = str(item.get("question_type", question_type)).strip() or question_type
        item_focus = str(item.get("focus_area", focus)).strip() or focus
        if not service.validate_question(question, item_focus or focus, item_type)[0]:
            continue
        if not service._topic_relevance(question, cv_context, jd_context, item_type, focus):
            continue
        if not service._soft_validate_question(question, role, cv_context, jd_context):
            continue
        if any(service.is_semantically_duplicate(question, existing["question"]) for existing in filtered if isinstance(existing, dict)):
            continue
        filtered.append({**item, "question": question, "question_type": item_type, "focus_area": item_focus})
        seen.add(lowered)
        if len(filtered) >= required_count:
            break
    return filtered


def is_duplicate(question: dict[str, object], existing: dict[str, object]) -> bool:
    return service.is_semantically_duplicate(service._question_text(question), service._question_text(existing)) or service.same_question_pattern(service._question_text(question), service._question_text(existing))


def deduplicate_questions(questions: list[dict[str, object]]) -> list[dict[str, object]]:
    unique: list[dict[str, object]] = []
    scenario_counts: service.Counter[str] = service.Counter()
    for question in questions:
        if not isinstance(question, dict):
            continue
        scenario_type = service._normalise_scenario_type(question.get("scenario_type"), str(question.get("question_type", "")))
        if scenario_counts[scenario_type] >= service.MAX_SCENARIO_TYPE_COUNT:
            continue
        if any(service.is_duplicate(question, existing) for existing in unique):
            continue
        unique.append({**question, "scenario_type": scenario_type, "dimension": service.DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery")})
        scenario_counts[scenario_type] += 1
    if len(unique) < 5:
        raise service.DuplicateQuestionError("Generated question set collapsed below five unique questions")
    return unique


def _validate_question_bundle(
    questions: list[dict[str, object]],
    *,
    role: str,
    cv_context: str,
    jd_context: str,
    expected_count: int | None = None,
) -> tuple[bool, str]:
    if len(questions) < 1 or len(questions) > 10 or (expected_count is not None and len(questions) != expected_count):
        return False, "invalid_question_count"

    scenario_types = [service._normalise_scenario_type(item.get("scenario_type"), str(item.get("question_type", ""))) for item in questions if isinstance(item, dict)]
    if any(count > service.MAX_SCENARIO_TYPE_COUNT for count in service.Counter(scenario_types).values()):
        return False, "duplicate_scenario_classification"
    if len(questions) >= 5 and set(scenario_types) != set(service.REQUIRED_SCENARIO_DIMENSIONS):
        return False, "missing_dimension_coverage"

    context_mode = service._context_mode(cv_context, jd_context)
    context_terms = service.resolve_missing_context(role, cv_context, jd_context)
    cv_keywords = set(context_terms["cv_keywords"])
    jd_keywords = set(context_terms["jd_keywords"])
    any_cv_grounding = False
    any_jd_grounding = False
    any_combined_grounding = False
    supported_terms = service._contextual_supported_terms(context_mode, role, cv_context, jd_context)

    for item in questions:
        if not isinstance(item, dict):
            return False, "invalid_question_item"
        question = service._question_text(item)
        cv_terms, jd_terms = service._source_terms(item)
        if any(term not in cv_context.lower() for term in cv_terms):
            return False, "unsupported_cv_source_terms"
        if any(term not in jd_context.lower() for term in jd_terms):
            return False, "unsupported_jd_source_terms"
        dimension = service._classify_dimension(item)
        if item.get("dimension") and str(item.get("dimension")).strip() != dimension:
            return False, "dimension_mismatch"
        if dimension not in service.DIMENSION_BY_SCENARIO_TYPE.values():
            return False, "invalid_dimension"
        if context_mode == "role_only":
            if has_unsupported_technology(question, role):
                return False, "scenario_a_contains_tech"
            if cv_terms or jd_terms:
                return False, "scenario_a_contains_source_terms"
        elif context_mode == "jd_only":
            if cv_terms:
                return False, "scenario_b_contains_cv_terms"
            if jd_keywords and not (jd_terms or service._has_allowed_term(question, supported_terms)):
                return False, "scenario_b_missing_jd_grounding"
        elif context_mode == "cv_jd":
            has_cv_signal = bool(cv_terms) or service._has_allowed_term(question, supported_terms | cv_keywords)
            has_jd_signal = bool(jd_terms) or service._has_allowed_term(question, supported_terms | jd_keywords)
            any_cv_grounding = any_cv_grounding or has_cv_signal
            any_jd_grounding = any_jd_grounding or has_jd_signal
            any_combined_grounding = any_combined_grounding or (has_cv_signal and has_jd_signal)
        elif context_mode == "cv_only":
            if jd_terms:
                return False, "scenario_cv_only_contains_jd_terms"
        if has_unsupported_technology(question, f"{role} {cv_context} {jd_context}"):
            return False, "hallucinated_tech"
        if len(questions) >= 5 and not service._has_supported_grounding(question, supported_terms):
            return False, "ungrounded_question"
        if len(questions) >= 5 and service._has_hallucinated_tech(question, supported_terms):
            return False, "hallucinated_tech"
        if dimension == "debugging / regression recovery" and "regression" not in question.lower() and "debug" not in question.lower():
            continue
    if context_mode == "cv_jd":
        if not any_cv_grounding:
            return False, "scenario_c_missing_cv_grounding"
        if not any_jd_grounding:
            return False, "scenario_c_missing_jd_grounding"
        if not any_combined_grounding:
            return False, "scenario_c_missing_alignment"
    return True, "valid"


def _raise_fallback_validation_error(reason: str) -> list[dict[str, object]]:
    service.LOGGER.error("Fallback generation failed validation: %s", reason)
    raise RuntimeError(f"Fallback generation failed validation: {reason}")


def _build_question_meta(items: list[dict[str, object]] | None) -> dict[str, object]:
    distribution = {key: 0 for key in ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")}
    questions = [item for item in items or [] if isinstance(item, dict)]
    for item in questions:
        question_type = str(item.get("question_type", "")).strip()
        if question_type in distribution:
            distribution[question_type] += 1
    return {"total_questions": len(questions), "distribution": distribution}

