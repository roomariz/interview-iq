"""Question generation job worker."""
from __future__ import annotations

from interview_app_backend.services import question_generation_job as _job_api


def _generate_question(payload: dict[str, _job_api.Any], generator=None) -> dict[str, _job_api.Any]:
    _job_api.clear_last_llm_call_metadata()
    try:
        generate = generator or _job_api.get_next_question_for_session
        bundle = generate(
            role=payload["role"],
            difficulty=payload["difficulty"],
            persona=payload["persona"],
            response_style=payload["response_style"],
            focus=payload["focus"],
            cv_context=payload["cv_context"],
            question_index=payload["question_index"],
            jd_context=payload["jd_context"],
            asked_topics=payload["asked_topics"],
            tech_stack=payload["tech_stack"],
            competencies=payload["competencies"],
            question_type=payload["question_type"],
            previous_questions=payload["previous_questions"],
            temperature=payload["temperature"],
            gap_analysis=payload["gap_analysis"],
            question_list_count=int(payload.get("question_list_count") or 5),
            return_meta=True,
            should_abort=payload.get("should_abort"),
        )
    except Exception as exc:
        if "Free model limit reached" in str(exc):
            return {
                "token": payload["token"],
                "status": "rate_limited",
                "error": "Free model limit reached. Try later.",
                "questions": [],
                "meta": {},
                "llm_metadata": _job_api.get_last_llm_call_metadata(),
            }
        _job_api.LOGGER.exception("Question generation failed, using fallback bundle")
        bundle = _job_api._build_fallback_questions(payload)
    if isinstance(bundle, dict):
        questions = bundle.get("questions", [])
        meta = bundle.get("meta", _job_api._build_question_meta(questions if isinstance(questions, list) else []))
    elif isinstance(bundle, list):
        questions = bundle
        meta = _job_api._build_question_meta(bundle)
    elif isinstance(bundle, str):
        questions = [{"question": bundle}]
        meta = _job_api._build_question_meta(questions)
    else:
        fallback_bundle = _job_api._build_fallback_questions(payload)
        questions = fallback_bundle["questions"]
        meta = fallback_bundle["meta"]
    expected_count = int(payload.get("question_list_count") or 5)
    if len(questions) != expected_count:
        _job_api.LOGGER.warning("Question job rejected partial result: expected=%s received=%s", expected_count, len(questions))
        questions = []
        meta = _job_api._build_question_meta([])
    return {
        "token": payload["token"],
        "questions": questions,
        "meta": meta,
        "llm_metadata": _job_api.get_last_llm_call_metadata(),
    }

