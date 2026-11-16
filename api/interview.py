"""Stateless adapters for the existing interview services."""

from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer
from fastapi import Security
from api.errors import SafeRoute

from config import settings
from config.model_profiles import get_question_count, is_free_model
from interview_app_backend.llm.client import clear_last_llm_call_metadata, get_last_llm_call_metadata
from interview_app_backend.llm.prompts.question_generation import (
    infer_competencies_from_context, infer_tech_stack_from_context, resolve_question_type,
)
from interview_app_backend.services import evaluation_service, question_service
from interview_app_backend.services.gap_analysis_service import analyse_gaps
from shared.api_contracts import (
    ContextRequest, ContextResponse, ErrorResponse, EvaluationRequest, EvaluationResponse,
    ExampleRequest, ExampleResponse, QuestionRequest, QuestionResponse,
)

router = APIRouter(prefix="/api/interview", route_class=SafeRoute, dependencies=[Security(HTTPBearer(auto_error=False))],
                   responses={code: {"model": ErrorResponse} for code in (401, 413, 422, 429, 502, 503, 504)})


@router.post("/context", response_model=ContextResponse)
def context(request: ContextRequest):
    competencies = infer_competencies_from_context(request.role, request.cv_context, request.jd_context)
    free = is_free_model(settings.MODEL_NAME)
    return ContextResponse(
        tech_stack=infer_tech_stack_from_context(request.cv_context, request.jd_context),
        competencies=competencies,
        question_type=resolve_question_type(request.question_type, competencies, request.cv_context, request.jd_context),
        gap_analysis=analyse_gaps(request.cv_context, request.jd_context),
        model=settings.MODEL_NAME, provider=settings.LLM_PROVIDER, free_mode=free,
        session_question_limit=get_question_count(settings.MODEL_NAME),
        question_list_count=1 if free else get_question_count(settings.MODEL_NAME),
    )


@router.post("/question", response_model=QuestionResponse)
def question(request: QuestionRequest):
    expected = 1 if is_free_model(settings.MODEL_NAME) else get_question_count(settings.MODEL_NAME)
    if request.question_list_count != expected:
        raise HTTPException(422, "question_count")
    clear_last_llm_call_metadata()
    result = question_service.get_next_question_for_session(**request.model_dump(), return_meta=True)
    if isinstance(result, str):
        result = {"questions": [{"question": result}], "meta": {}}
    elif isinstance(result, list):
        result = {"questions": result, "meta": {}}
    if not isinstance(result, dict) or len(result.get("questions", [])) != expected:
        raise HTTPException(502, "invalid_provider_result")
    # Existing services validate quality, grounding, duplicates and exact schema.
    response = QuestionResponse.model_validate({**result, "llm_metadata": get_last_llm_call_metadata()})
    distribution = dict.fromkeys(("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"), 0)
    for item in response.questions:
        kind = getattr(item, "question_type", "")
        if kind in distribution:
            distribution[kind] += 1
    response.meta = {**response.meta, "total_questions": expected, "distribution": distribution}
    return response


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest):
    result = evaluation_service.evaluate_submission(request.question, request.answer)
    return EvaluationResponse.model_validate(result)


@router.post("/example-answer", response_model=ExampleResponse)
def example_answer(request: ExampleRequest):
    if is_free_model(settings.MODEL_NAME):
        return ExampleResponse(text="Example answers are unavailable in free mode.")
    return ExampleResponse(text=evaluation_service.generate_example_answer(request.answer))
