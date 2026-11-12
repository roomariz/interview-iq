import json
import re

from interview_app_backend.llm.client import call_llm, get_openrouter_client
from interview_app_backend.llm.parser import parse_evidence_response, parse_json_response
from interview_app_backend.llm.prompts.interview import (
    build_example_answer_prompt,
    build_reference_answer_prompt,
    build_semantic_similarity_prompt,
)
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
from config.settings import PRIMARY_PROVIDER


EVALUATION_PROVIDER = PRIMARY_PROVIDER


def _get_evaluation_client():
    if EVALUATION_PROVIDER == "open-router":
        return get_openrouter_client()
    return get_openrouter_client()


EVIDENCE_EXTRACTION_PROMPT = (
    "Extract structured evidence from the candidate answer. Return ONLY valid JSON.\n\n"
    "JSON schema:\n"
    "{"
    '"has_metrics":false,'
    '"metrics":[{"type":"","before":"","after":"","change":""}],'
    '"has_structure":false,'
    '"has_reasoning":false,'
    '"has_tradeoffs":false,'
    '"has_alternatives":false,'
    '"confidence":{"metrics":0,"structure":0,"reasoning":0,"tradeoffs":0,"alternatives":0},'
    '"anomaly_flags":[]'
    "}\n\n"
    "Rules:\n"
    "- Set has_metrics true when the answer includes numbers, percentages, before/after values, time, cost, scale, throughput, latency, CPU, error rate, or other measurable impact.\n"
    "- Capture metrics even when they are phrased as ranges, approximations, or before/after comparisons.\n"
    "- Mark ambiguous, fake-looking, or non-impact numbers in anomaly_flags instead of treating them as strong metrics.\n"
    "- Flag negative or misleading metric phrasing when the number shape conflicts with the described outcome.\n"
    "- Set has_structure true when the answer has clear sections such as Challenge, Approach, Results, Situation, Task, Action, Result, or equivalent flow.\n"
    "- Set has_reasoning true when the answer explains why decisions were made.\n"
    "- Set has_tradeoffs true when the answer mentions trade-offs, risks, complexity, consistency, or budget constraints.\n"
    "- Set has_alternatives true when the answer mentions considered or rejected alternatives.\n"
    "- Do not invent evidence.\n"
    "- Return JSON only."
)

EVALUATION_PROMPT = (
    "Evaluate the candidate answer. Return ONLY valid JSON.\n\n"
    "JSON schema:\n"
    "{"
    '"evaluation":{"overall_decision":"pass|borderline pass|fail","scores":{"relevance":0,"structure":0,"specificity":0,"communication":0,"problem_solving_approach":0},"labels":{"relevance":"","structure":"","specificity":"","communication":"","problem_solving_approach":""}},'
    '"summary":"",'
    '"key_issues":[],'
    '"improvements":[],'
    '"reasoning":{"clarity":"","alternative_approaches":"","trade_off_awareness":"","evidence":""},'
    '"follow_up":{"question":"","type":"","target_dimension":""},'
    '"topic_match":true,'
    '"relevance_gate_applied":false,'
    '"trust":{"trust_level":"","trust_definition":"","score_confidence":0,"decision_confidence":"","impact_strength":"","reason":""}'
    "}\n\n"
    "Scoring rules:\n"
    "- Before identifying weaknesses, use the extracted evidence context as the source of truth.\n"
    "- Do not say a metric is missing if the answer includes numbers, percentages, before/after values, time, cost, scale, throughput, latency, CPU, error rate, or other measurable impact.\n"
    '- If measurable results are present but could be stronger, say: "Metrics are present, but could be tied more clearly to business or user impact."\n'
    "- Specificity rubric:\n"
    "  - 8-10: Multiple concrete measurable outcomes with clear before/after or percentage change.\n"
    "  - 5-7: Some metrics, but linkage or coverage is incomplete.\n"
    "  - 0-4: No measurable evidence.\n"
    "  - Do not assign a score below 7 if multiple valid metrics are present.\n"
    "- Structure rubric:\n"
    "  - 8-10: Clear STAR or equivalent structure.\n"
    "  - 6-7: Partial structure, challenge plus approach plus results are present.\n"
    "  - 0-5: Disorganised.\n"
    "  - If Challenge, Approach, and Results are present, do not score structure below 6.\n"
    "- Problem-solving rubric:\n"
    "  - 8-10: Explains decisions, trade-offs, and alternatives.\n"
    "  - 5-7: Good approach but reasoning is implicit.\n"
    "  - 0-4: Steps listed without explanation.\n"
    "Inputs:\n"
    "- Question\n"
    "- Candidate Answer\n"
    "- Reference Answer (guideline only)\n"
    "- Semantic Similarity Score (0–1)\n\n"
    "Similarity (supporting only):\n"
    ">=0.75 strong, 0.4–0.74 partial, <0.4 weak\n"
    "- Do NOT rely only on similarity\n\n"
    "Rules:\n"
    "- Base evaluation ONLY on explicit evidence in the answer\n"
    "- Do NOT ignore metrics, results, or technical details present\n"
    "- Do NOT invent missing issues\n"
    "- Reference answer is NOT ground truth\n"
    "- Valid alternative approaches must not be penalised\n\n"
    "- Only refer to concepts explicitly present in the answer. Do NOT introduce technologies, techniques, or scenarios not mentioned.\n"
    "Prompt requirements:\n"
    "- Cross-check key issues and improvements against the extracted evidence context before finalising them.\n"
    "- Treat evaluation_context as structured support, not as a score override.\n"
    "- Treat evaluation_context as the source of truth for trust, confidence, and follow-up fields.\n"
    "- Surface contradiction flags and anomaly flags in the returned JSON when they are present.\n"
    "- Remove any issue that contradicts the answer content.\n"
    "- If the answer gives technical actions but limited reasoning, focus weaknesses on why each solution was chosen, trade-offs accepted, and alternatives considered and rejected.\n"
    "- technical_accuracy: correctness of solution\n"
    "- clarity: how clearly explained\n"
    "- structure: organisation and flow\n"
    "- relevance: alignment with question\n"
    "- problem_solving_approach: reasoning, trade-offs, justification\n\n"
    "Output:\n"
    "- strengths: 2–3 concise points\n"
    "- improvement_areas: 2–3 actionable points\n"
    "- overall_summary: 1–2 sentences\n\n"
    "- evaluation_version: short version tag for the evaluation contract\n"
    "- evaluation_trace: ordered steps showing how the result was interpreted\n"
    "- impact_strength: weak, moderate, or strong\n\n"
    "Return JSON only."
)

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
) -> dict:
    if not is_answer_relevant(question, answer):
        return build_relevance_gate_evaluation(question, answer)
    client = _get_evaluation_client()
    evaluation_context = extract_evidence_context(question, answer, client=client)
    evaluation_context["topic_match"] = True
    prompt = EVALUATION_PROMPT + "\n\nEvaluation context:\n" + json.dumps(evaluation_context, ensure_ascii=True)
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
    evaluation = ground_evaluation_result(evaluation, evaluation_context)
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
    return payload.strip()


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
