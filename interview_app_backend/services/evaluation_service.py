import json
import re

from interview_app_backend.llm.client import call_llm, get_openrouter_client
from interview_app_backend.llm.parser import parse_evidence_response, parse_json_response
from interview_app_backend.llm.prompts.evaluation import EVIDENCE_EXTRACTION_PROMPT, EVALUATION_PROMPT
from interview_app_backend.llm.prompts.interview import (
    build_example_answer_prompt,
    build_reference_answer_prompt,
    build_semantic_similarity_prompt,
)
from interview_app_backend.services.feedback_support import validate_feedback_support
from interview_app_backend.services.feedback_integrity import example_text, clean_feedback
from interview_app_backend.services.feedback_repair import repair_feedback, criteria_for_type
from interview_app_backend.services.evaluation_grounding import ground_evaluation_result
from interview_app_backend.services.evaluation_pipeline import EvaluationPipeline
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation
from interview_app_backend.services.evaluation_rules import (
    build_evaluation_context,
    build_normalisation,
    build_overall_decision_detail,
    derive_overall_decision,
    is_answer_relevant,  # noqa: F401
)
from interview_app_backend.services.relevance_assessment import QUESTION_CRITERIA, validate_scoring_relevance
from config.settings import PRIMARY_PROVIDER


EVALUATION_PROVIDER = PRIMARY_PROVIDER


def _get_evaluation_client():
    if EVALUATION_PROVIDER == "open-router":
        return get_openrouter_client()
    return get_openrouter_client()




def extract_evidence_context(question: str, answer: str, client=None) -> dict:
    client = client or _get_evaluation_client()
    payload = call_llm(
        f"{EVIDENCE_EXTRACTION_PROMPT}\n\nQuestion:\n{question}\n\nAnswer:\n{answer}",
        client,
        temperature=0,
        task="evaluation.evidence_extraction",
    )
    return build_evaluation_context(parse_evidence_response(payload), answer=answer)


def evaluate_answer(
    question: str,
    answer: str,
    reference_answer: str | None = None,
    semantic_similarity_score: float | None = None,
    relevance_assessment: dict | None = None,
) -> dict:
    assessment = relevance_assessment if relevance_assessment is not None else is_answer_relevant(question, answer, True)
    if isinstance(assessment, bool):
        assessment = {"status": "relevant" if assessment else "off_topic", "question_type": "behavioural"}
    if assessment["status"] == "off_topic":
        return build_relevance_gate_evaluation(question, answer)
    client = _get_evaluation_client()
    evaluation_context = extract_evidence_context(question, answer, client=client)
    evaluation_context.update(topic_match=True, question_type=assessment.get("question_type", "other"),
                              relevance_assessment=assessment)
    prompt = EVALUATION_PROMPT + "\n" + QUESTION_CRITERIA + "\n" + (
        "For non-behavioural questions, specificity means concrete applicable steps, evidence and decisions; "
        "structure means coherent explanation or diagnostic sequence. Historical metrics and STAR are not required. "
        "The relevance assessment is authoritative for gate decisions. Do not conflate low quality with off-topic. "
        "Follow-ups must reference the actual question and answer; never invent a past experience requirement. "
    ) + "\n\nEvaluation context:\n" + json.dumps(evaluation_context, ensure_ascii=True)
    if reference_answer is not None:
        prompt += f"\n\nReference answer:\n{reference_answer.strip()}"
    if semantic_similarity_score is not None:
        prompt += f"\nSemantic similarity score: {semantic_similarity_score:.2f}"
    payload = call_llm(
        f"{prompt}\n\nQuestion:\n{question}\n\nAnswer:\n{answer}",
        client,
        task="evaluation.scoring",
    )
    evaluation = parse_json_response(payload)
    validate_scoring_relevance(payload, evaluation, question)
    evaluation.update(question=question, answer=answer, relevance_assessment=assessment)
    evaluation = clean_feedback(evaluation)
    try:
        raw = json.loads(payload)
    except (ValueError, TypeError):
        raw = {}
    evaluation = validate_feedback_support(evaluation, raw, question, answer)
    evaluation = repair_feedback(evaluation, question, answer, client, call_llm)
    evaluation = ground_evaluation_result(evaluation, evaluation_context)
    evaluation["criteria"] = criteria_for_type(assessment.get("question_type", "other"))
    evaluation.update(topic_match=True, relevance_gate_applied=False)
    evaluation["overall_decision"] = derive_overall_decision(evaluation.get("scores", {}))
    validation_warning = evaluation.get("validation_warning", {})
    evaluation["overall_decision_detail"] = build_overall_decision_detail(
        evaluation.get("scores", {}),
        trust_level=str(validation_warning.get("trust_level", "high")),
        score_confidence=validation_warning.get("score_confidence"),
    )
    normalisation = build_normalisation(evaluation.get("scores", {}))
    evaluation["normalisation"] = normalisation
    evaluation["normalised_score_detail"] = normalisation.get("detail")
    evaluation["evaluation_context"] = evaluation_context
    evaluation["evaluation_version"] = evaluation_context.get("evaluation_version", "")
    evaluation["evaluation_trace"] = evaluation_context.get("evaluation_trace", [])
    evaluation["impact_strength"] = evaluation_context.get("impact_strength", "")
    evaluation["answer"] = answer
    return evaluation


def generate_example_answer(answer: str) -> str:
    try:
        client = _get_evaluation_client()
    except ValueError:
        return answer.strip()
    payload = call_llm(build_example_answer_prompt(answer), client, task="evaluation.example_answer")
    return example_text(payload)


def generate_reference_answer(question: str) -> str:
    try:
        client = _get_evaluation_client()
    except (TypeError, ValueError):
        return ""
    payload = call_llm(build_reference_answer_prompt(question), client, temperature=0, task="evaluation.reference_answer")
    return payload.strip()


def _parse_similarity_score(payload: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", payload)
    if not match:
        return 0.0
    score = float(match.group(0))
    return max(0.0, min(1.0, score))


def calculate_semantic_similarity(reference_answer: str, user_answer: str) -> float:
    if not reference_answer.strip() or not user_answer.strip():
        return 0.0
    try:
        client = _get_evaluation_client()
    except (TypeError, ValueError):
        return 0.0
    payload = call_llm(
        build_semantic_similarity_prompt(reference_answer, user_answer),
        client,
        temperature=0,
        task="evaluation.semantic_similarity",
    )
    return _parse_similarity_score(payload)


def evaluate_submission(question: str, answer: str) -> dict:
    try:
        evaluation = EvaluationPipeline().run(question, answer)
    except ValueError:
        return {
            "question": question,
            "answer": answer,
            "reference_answer": "",
            "semantic_similarity_score": 0.0,
        }

    return evaluation
