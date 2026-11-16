"""Bounded question generation with precise validation feedback on each retry."""

from __future__ import annotations

import json

from interview_app_backend.llm.deadline import check

from interview_app_backend.llm.question_contract import (
    QuestionValidationError, contract_header, distribution_for, validate_question_response,
)
from interview_app_backend.services import question_service as service
from interview_app_backend.services.question_validation import validate_generated_items


def _generate_with_retry(
    prompt: str, client: object, role: str, difficulty: str, focus: str,
    cv_context: str, jd_context: str, question_type: str, question_index: int = 1,
    previous_questions: list[str] | None = None, question_plan: dict[str, object] | None = None,
    temperature: object | None = None, question_list_count: int = 1,
    retries: int | None = None, return_meta: bool = False, use_provider_fallback: bool = True,
    should_abort: service.Callable[[], bool] | None = None,
) -> str | list[dict[str, object]] | dict[str, object]:
    retries = service._question_retry_limit() if retries is None else retries
    count = question_list_count
    expected_distribution = distribution_for(count, question_type)
    # The transport schema reads this trusted first line, including on correction attempts.
    if prompt.startswith("QUESTION_CONTRACT:"):
        prompt = prompt.split("\n", 1)[1]
    base_prompt = contract_header(count, question_type) + "\n" + prompt
    attempt_prompt = base_prompt
    strict = service._question_strict_json()
    for attempt in range(retries + 1):
        check()
        if should_abort and should_abort():
            raise RuntimeError("cancelled")
        try:
            response = service.call_llm(
                attempt_prompt, client, temperature=service._normalise_temperature(temperature),
                task=f"question_generation.{question_type}",
                provider="open-router" if use_provider_fallback else None,
                should_abort=should_abort if callable(should_abort) else None,
            )
            if should_abort and should_abort():
                raise RuntimeError("cancelled")
            if strict:
                bundle = validate_question_response(response, count, expected_distribution)
                items = bundle["questions"]
                meta = bundle["meta"]
            else:
                try:
                    json.loads(response)
                except (ValueError, TypeError) as exc:
                    raise QuestionValidationError("invalid_json: return one complete JSON document") from exc
                items = service.parse_question_generation_response(response, strict=False)
                meta = service._build_question_meta(items)
            validate_generated_items(items, count=count, role=role, cv_context=cv_context,
                                     jd_context=jd_context, previous_questions=previous_questions)
            service.LOGGER.info("Question bundle validated: requested=%s received=%s attempt=%s", count, len(items), attempt + 1)
            if count == 1 and not return_meta:
                return service._question_text(items[0])
            return {"questions": items, "meta": meta} if return_meta else items
        except (QuestionValidationError, StopIteration, RuntimeError) as exc:
            if str(exc) == "cancelled" or "Free model limit reached" in str(exc):
                raise
            validation = exc if isinstance(exc, QuestionValidationError) else exc.__cause__
            reason = str(validation) if isinstance(validation, QuestionValidationError) else "provider_request_failed"
            service.LOGGER.warning("Question attempt rejected: attempt=%s expected=%s reason=%s", attempt + 1, count, reason)
            attempt_prompt = (base_prompt + "\nRETRY_CORRECTION: " + reason +
                              f"\nReturn a complete replacement with exactly {count} questions and the exact requested distribution. "
                              "Correct the failed rule; do not return a partial set or append only the missing questions.")
            if not isinstance(exc, QuestionValidationError) and service._is_permanent_error(exc.__cause__ or exc):
                break
    if should_abort and should_abort():
        raise RuntimeError("cancelled")
    service.clear_last_llm_call_metadata()
    if count > 1:
        items = service._validated_fallback_bundle(
            role=role, difficulty=difficulty, focus=focus, cv_context=cv_context, jd_context=jd_context,
            question_type=question_type, previous_questions=previous_questions, question_plan=question_plan, required_count=count,
        )
        return {"questions": items, "meta": service._build_question_meta(items)} if return_meta else items
    question = service.generate_safe_fallback(
        role=role, difficulty=difficulty, focus=focus, cv_context=cv_context, jd_context=jd_context,
        question_type=question_type, question_index=question_index,
        previous_questions=previous_questions, question_plan=question_plan,
    )
    valid, reason = service._validate_single_question(question, role=role, cv_context=cv_context,
                                                      jd_context=jd_context, focus=focus, question_type=question_type)
    if not valid or service._is_similar_to_previous(question, previous_questions):
        service._raise_fallback_validation_error(reason if not valid else "duplicate_previous_question")
    if return_meta:
        item = service._question_item(question, question_plan or {"question_type": "cv_based", "difficulty": difficulty, "purpose": focus})
        return {"questions": [item], "meta": service._build_question_meta([item])}
    return question
