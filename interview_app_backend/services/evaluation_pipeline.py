from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_decisions import apply_decision_adjustments, build_evaluation_summary
from interview_app_backend.services.evaluation_grounding import ground_evaluation_result
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation
from interview_app_backend.services.relevance_preclassifier import classify_relevance
from interview_app_backend.services.evaluation_rules import classify_fallback_failure
from interview_app_backend.services.pipeline_output import (
    attach_pipeline, attach_relevance_gate, _grounding_score, _evaluation_confidence,
)
from interview_app_backend.utils.validation import block_prompt_injection, validate_answer_length, validate_text
from config.model_profiles import is_free_model
from config.settings import MODEL_NAME

class EvaluationPipeline:
    def run(self, question: str, answer: str) -> dict[str, Any]:
        input_state = self.validate_input(question, answer)
        relevance_state = self.run_relevance_stage(input_state["question"], input_state["answer"])
        if not relevance_state["combined_verdict"]:
            result = build_relevance_gate_evaluation(input_state["question"], input_state["answer"])
            result["reference_answer"] = ""
            result["semantic_similarity_score"] = 0.0
            result = attach_relevance_gate(result, input_state, relevance_state)
            result["example_answer"] = ""
            return attach_pipeline(result, input_state, relevance_state, grounded=False)

        from interview_app_backend.services import evaluation_service as service

        if is_free_model(MODEL_NAME):
            reference_answer = ""
            semantic_similarity_score = 0.0
        else:
            reference_answer = service.generate_reference_answer(input_state["question"])
            semantic_similarity_score = service.calculate_semantic_similarity(reference_answer, input_state["answer"])
        try:
            result = service.evaluate_answer(
                input_state["question"],
                input_state["answer"],
                reference_answer=reference_answer,
                semantic_similarity_score=semantic_similarity_score,
                relevance_assessment=relevance_state["assessment"],
            )
        except Exception as exc:
            raise RuntimeError("Evaluation unavailable. Please try again; no scores were recorded.") from exc
        result["reference_answer"] = reference_answer
        result["semantic_similarity_score"] = semantic_similarity_score
        result = self._ground_and_enrich(result, input_state, relevance_state)
        return attach_pipeline(result, input_state, relevance_state, grounded=True)

    def validate_input(self, question: str, answer: str) -> dict[str, Any]:
        question_text = question.strip()
        answer_text = answer.strip()
        issues: list[str] = []
        if not validate_text(question_text):
            issues.append("empty_question")
        if not validate_text(answer_text):
            issues.append("empty_answer")
        if not validate_answer_length(answer_text):
            issues.append("answer_length")
        if not block_prompt_injection(answer_text):
            issues.append("prompt_injection")
        return {"question": question_text, "answer": answer_text, "issues": issues, "blocked": bool(issues)}

    def run_relevance_stage(self, question: str, answer: str) -> dict[str, Any]:
        preclassification = classify_relevance(question, answer)
        from interview_app_backend.services import evaluation_service as service

        assessment = service.is_answer_relevant(question, answer, True)
        if isinstance(assessment, bool):
            assessment = {"status": "relevant" if assessment else "off_topic",
                          "confidence": 0.75 if assessment else 0.9, "question_type": "behavioural"}
        combined_verdict = assessment["status"] != "off_topic"
        conflict = bool(preclassification["match"]) != combined_verdict
        confidence = float(assessment.get("confidence", 0.0))
        if assessment["status"] == "uncertain":
            confidence = min(confidence, 0.49)
        return {
            "assessment": assessment,
            "preclassification": preclassification,
            "combined_verdict": combined_verdict,
            "conflict": conflict,
            "confidence": confidence,
        }

    def _ground_and_enrich(self, result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        evaluation = dict(result)
        evaluation.update(question=input_state["question"], answer=input_state["answer"])
        evaluation["relevance_assessment"] = relevance_state["assessment"]
        evaluation_context = dict(evaluation.get("evaluation_context", {}))
        if relevance_state.get("conflict"):
            anomaly_flags = list(evaluation_context.get("anomaly_flags", []))
            if "classifier_conflict" not in anomaly_flags:
                anomaly_flags.append("classifier_conflict")
            evaluation_context["anomaly_flags"] = anomaly_flags
            evaluation = ground_evaluation_result(evaluation, evaluation_context)
            evaluation["evaluation_context"] = evaluation_context
        follow_up = self._ground_follow_up(evaluation, input_state, relevance_state)
        evaluation["follow_up"] = follow_up
        grounding_score = _grounding_score(evaluation)
        evaluation["grounding_score"] = grounding_score
        evaluation["evaluation_confidence"] = _evaluation_confidence(evaluation, relevance_state, grounding_score)
        evaluation["failure_type"] = classify_fallback_failure(evaluation.get("scores", {}), evaluation_context.get("topic_match", True), bool(evaluation.get("relevance_gate_applied")))
        evaluation = apply_decision_adjustments(evaluation, evaluation["evaluation_confidence"], grounding_score)
        evaluation["evaluation_summary"] = build_evaluation_summary(evaluation, evaluation["failure_type"], evaluation["evaluation_confidence"], grounding_score)
        return evaluation



    def _ground_follow_up(self, evaluation: Mapping[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        from interview_app_backend.services.question_followup import question_bound_followup

        return question_bound_followup(input_state["question"], input_state["answer"], relevance_state["assessment"], evaluation.get("feedback", {}))
