"""Question generation fallback."""

from __future__ import annotations

from interview_app_backend.services import question_service as service
from interview_app_backend.llm.question_contract import (
    QuestionValidationError, distribution_for, validate_question_response,
)
from interview_app_backend.services.question_validation import validate_generated_items


def _validated_fallback_bundle(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int,
) -> list[dict[str, object]]:
    fallback_items = service._fallback_question_items(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        previous_questions=previous_questions,
        question_plan=question_plan,
        required_count=required_count,
    )
    try:
        wire_items = [{key: value for key, value in item.items() if key != "dimension"} for item in fallback_items]
        validate_question_response(service.json.dumps({"meta": service._build_question_meta(fallback_items), "questions": wire_items}),
                                   required_count, distribution_for(required_count, question_type))
        validate_generated_items(fallback_items, count=required_count, role=role, cv_context=cv_context,
                                 jd_context=jd_context, previous_questions=previous_questions)
    except QuestionValidationError as exc:
        service._raise_fallback_validation_error(str(exc))
    return fallback_items


def _fallback_question_items(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int,
) -> list[dict[str, object]]:
    fallback: list[dict[str, object]] = []
    previous: list[str] = list(previous_questions or [])
    count = required_count or 5
    fallback_question_types = ["cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"]
    base_plan = question_plan or service._build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=[],
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    for index in range(1, count + 1):
        generated_question_type = fallback_question_types[(index - 1) % len(fallback_question_types)]
        scenario_type = service.QUESTION_TYPE_TO_SCENARIO_TYPE.get(generated_question_type, "debugging")
        item_focus = "performance" if scenario_type == "performance" else scenario_type
        item_plan = service._build_question_plan(
            role=role,
            difficulty=difficulty,
            question_index=index,
            cv_context=cv_context,
            jd_context=jd_context,
            asked_topics=[],
            focus=item_focus,
            question_type=generated_question_type,
            previous_questions=previous,
        )
        item_plan = {**base_plan, **item_plan, "question_index": index, "question_type": generated_question_type}
        question = service.generate_safe_fallback(
            role=role,
            difficulty=difficulty,
            focus=item_focus,
            cv_context=cv_context,
            jd_context=jd_context,
            question_type=generated_question_type,
            question_index=index,
            previous_questions=previous,
            question_plan=item_plan,
        )
        if not question or question.lower() in {entry.lower() for entry in previous}:
            continue
        previous.append(question)
        fallback.append(service._question_item(question, item_plan))
        fallback[-1]["scenario_type"] = scenario_type
        fallback[-1]["dimension"] = service.DIMENSION_BY_SCENARIO_TYPE[scenario_type]
        fallback[-1]["sequence_order"] = index
    return fallback[:10]


def fallback_questions(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int = 5,
) -> list[dict[str, object]]:
    return service._validated_fallback_bundle(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        previous_questions=previous_questions,
        question_plan=question_plan,
        required_count=required_count,
    )

