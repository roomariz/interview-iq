"""Question generation session requests."""

from __future__ import annotations

from interview_app_backend.services import question_service as service


def get_role_based_question(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    focus: str = "General",
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
    question_list_count: int = 1,
) -> str | list[dict[str, object]]:
    plan = service._build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    prompt = service.build_role_based_question_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        asked_topics=list(plan["asked_topics"]),
        focus=str(plan["focus"]),
        tech_stack=tech_stack,
        competencies=competencies,
        question_type=str(plan["question_type"]),
        previous_questions=list(plan["previous_questions"]),
        temperature=temperature,
        gap_analysis=gap_analysis,
        question_count=question_list_count,
    )
    client = service._get_client_or_none()
    if client is None:
        if question_list_count > 1:
            return service._validated_fallback_bundle(
                role=str(plan["role"]),
                difficulty=str(plan["difficulty"]),
                focus=str(plan["focus"]),
                cv_context=str(plan["cv_context"]),
                jd_context=str(plan["jd_context"]),
                question_type=str(plan["question_type"]),
                previous_questions=list(plan["previous_questions"]),
                question_plan=plan,
                required_count=question_list_count,
            )
        fallback_question = service.generate_safe_fallback(
            role=str(plan["role"]),
            difficulty=str(plan["difficulty"]),
            focus=str(plan["focus"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            question_type=str(plan["question_type"]),
            question_index=1,
            previous_questions=list(plan["previous_questions"]),
            question_plan=plan,
        )
        valid, reason = service._validate_single_question(
            fallback_question,
            role=str(plan["role"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            focus=str(plan["focus"]),
            question_type=str(plan["question_type"]),
        )
        if not valid:
            service._raise_fallback_validation_error(reason)
        return fallback_question
    return service._generate_with_retry(
        prompt=prompt,
        client=client,
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        focus=str(plan["focus"]),
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        question_type=str(plan["question_type"]),
        question_index=1,
        previous_questions=list(plan["previous_questions"]),
        question_plan=plan,
        temperature=temperature,
        question_list_count=question_list_count,
        use_provider_fallback=True,
    )


def get_next_question_for_session(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    focus: str,
    cv_context: str,
    question_index: int,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
    question_list_count: int = 1,
    return_meta: bool = False,
    should_abort: service.Callable[[], bool] | None = None,
) -> str | list[dict[str, object]] | dict[str, object]:
    if not isinstance(question_index, int):
        raise ValueError("question_index must be int")
    if question_index < 1:
        raise ValueError("question_index must be at least 1")

    plan = service._build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    prompt = service.build_question_generation_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        temperature=temperature if temperature is not None else 0.7,
        cv_profile=str(plan["cv_context"]),
        job_description=str(plan["jd_context"]),
        gap_analysis=gap_analysis or {"focus": str(plan["focus"]), "focus_area": str(plan["focus_area"]), "question_type": str(plan["question_type"])},
        prompt_style=service._question_prompt_style(),
        question_count=question_list_count,
        question_type=str(plan["question_type"]),
    )

    client = service._get_client_or_none()
    if client is None:
        if question_list_count > 1:
            return service._validated_fallback_bundle(
                role=str(plan["role"]),
                difficulty=str(plan["difficulty"]),
                focus=str(plan["focus"]),
                cv_context=str(plan["cv_context"]),
                jd_context=str(plan["jd_context"]),
                question_type=str(plan["question_type"]),
                previous_questions=list(plan["previous_questions"]),
                question_plan=plan,
                required_count=question_list_count,
            )
        fallback_question = service.generate_safe_fallback(
            role=str(plan["role"]),
            difficulty=str(plan["difficulty"]),
            focus=str(plan["focus"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            question_type=str(plan["question_type"]),
            question_index=question_index,
            previous_questions=list(plan["previous_questions"]),
            question_plan=plan,
        )
        valid, reason = service._validate_single_question(
            fallback_question,
            role=str(plan["role"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            focus=str(plan["focus"]),
            question_type=str(plan["question_type"]),
        )
        if not valid:
            service._raise_fallback_validation_error(reason)
        return fallback_question
    return service._generate_with_retry(
        prompt=prompt,
        client=client,
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        focus=str(plan["focus"]),
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        question_type=str(plan["question_type"]),
        question_index=question_index,
        previous_questions=list(plan["previous_questions"]),
        question_plan=plan,
        temperature=temperature,
        question_list_count=question_list_count,
        return_meta=return_meta,
        use_provider_fallback=True,
        should_abort=should_abort,
    )

