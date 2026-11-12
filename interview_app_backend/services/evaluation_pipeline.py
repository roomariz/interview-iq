from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_decisions import apply_decision_adjustments, build_evaluation_summary, classify_failure_type
from interview_app_backend.services.evaluation_grounding import ground_evaluation_result
from interview_app_backend.services.relevance_gate import build_relevance_gate_evaluation
from interview_app_backend.services.relevance_preclassifier import classify_relevance
from interview_app_backend.services.evaluation_rules import build_normalisation
from interview_app_backend.services.evaluation_rules import classify_fallback_failure
from interview_app_backend.services.trust_defaults import build_fallback_review_state
from interview_app_backend.utils.validation import block_prompt_injection, validate_answer_length, validate_text
from config.model_profiles import is_free_model
from config.settings import MODEL_NAME

_DIMENSIONS = ("relevance", "structure", "specificity", "communication", "problem_solving_approach")


class EvaluationPipeline:
    def run(self, question: str, answer: str) -> dict[str, Any]:
        input_state = self.validate_input(question, answer)
        relevance_state = self.run_relevance_stage(input_state["question"], input_state["answer"])
        if not relevance_state["combined_verdict"]:
            result = build_relevance_gate_evaluation(input_state["question"], input_state["answer"])
            result["reference_answer"] = ""
            result["semantic_similarity_score"] = 0.0
            result = self._attach_relevance_gate(result, input_state, relevance_state)
            result["example_answer"] = ""
            return self._attach_pipeline(result, input_state, relevance_state, grounded=False)

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
            )
        except Exception as exc:
            return self._degraded_evaluation(input_state["question"], input_state["answer"], str(exc), relevance_state)
        result["reference_answer"] = reference_answer
        result["semantic_similarity_score"] = semantic_similarity_score
        result = self._ground_and_enrich(result, input_state, relevance_state)
        return self._attach_pipeline(result, input_state, relevance_state, grounded=True)

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

        combined_verdict = bool(service.is_answer_relevant(question, answer))
        conflict = bool(preclassification["match"]) != combined_verdict
        confidence = self._relevance_confidence(preclassification, combined_verdict, conflict)
        return {
            "preclassification": preclassification,
            "combined_verdict": combined_verdict,
            "conflict": conflict,
            "confidence": confidence,
        }

    def _relevance_confidence(self, preclassification: Mapping[str, Any], combined_verdict: bool, conflict: bool) -> float:
        if conflict:
            return 0.45 if combined_verdict else 0.2
        if combined_verdict and preclassification.get("confidence") == "high":
            return 0.9
        if combined_verdict:
            return 0.75
        if preclassification.get("confidence") == "high":
            return 0.15
        return 0.35

    def _ground_and_enrich(self, result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        evaluation = dict(result)
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
        grounding_score = self._grounding_score(evaluation)
        evaluation["grounding_score"] = grounding_score
        evaluation["evaluation_confidence"] = self._evaluation_confidence(evaluation, relevance_state, grounding_score)
        evaluation["failure_type"] = classify_fallback_failure(evaluation.get("scores", {}), evaluation_context.get("topic_match", True), bool(evaluation.get("relevance_gate_applied")))
        evaluation = apply_decision_adjustments(evaluation, evaluation["evaluation_confidence"], grounding_score)
        evaluation["evaluation_summary"] = build_evaluation_summary(evaluation, evaluation["failure_type"], evaluation["evaluation_confidence"], grounding_score)
        return evaluation

    def _attach_relevance_gate(self, result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        evaluation = dict(result)
        evaluation["topic_match"] = False
        evaluation["relevance_gate_applied"] = True
        evaluation["failure_type"] = "off_topic"
        evaluation["overall_decision"] = "fail"
        evaluation["overall_decision_detail"] = {
            "value": "fail",
            "score_based_value": "fail",
            "trust_level": "low",
            "score_confidence": 0.0,
            "decision_confidence": "high",
            "gating_applied": True,
            "reason": "The answer is not relevant to the question.",
        }
        evaluation["trust"] = {
            "trust_level": "low",
            "trust_definition": "Low evaluation depth but high decision confidence because the answer is not relevant to the question.",
            "score_confidence": 0.0,
            "decision_confidence": "high",
            "impact_strength": "unknown",
            "reason": "The answer is not relevant to the question, so the off-topic decision is certain.",
        }
        evaluation["validation_warning"] = {
            "severity": "info",
            "trust_level": "low",
            "score_confidence": 0.0,
            "reasoning_depth": "not_applicable",
            "interpretation": "This answer is not relevant to the question, so detailed evaluation is not applicable.",
            "has_warning": True,
            "anomaly_flags": ["off_topic"],
            "validation": {
                "severity": "info",
                "severity_definition": "Expected behaviour; the answer is not relevant to the question.",
                "trust_level": "low",
                "trust_definition": evaluation["trust"]["trust_definition"],
                "score_confidence": 0.0,
                "impact_strength": "unknown",
                "anomaly_influence": {},
            },
        }
        evaluation["feedback"] = {
            "summary": "The answer is not relevant to the question.",
            "strengths": [],
            "key_issues": ["The answer is not relevant to the question."],
            "improvements": ["Use a concrete example that answers the system-performance question directly."],
        }
        evaluation["reasoning"] = {
            "clarity": "The response does not answer the prompt directly.",
            "alternative_approaches": "Not assessed because the answer is not relevant to the question.",
            "trade_off_awareness": "Not assessed because the answer is not relevant to the question.",
            "evidence": "No supported evidence for the requested topic was provided.",
        }
        evaluation["follow_up"] = {
            "question": "How would you adapt this example to demonstrate system performance improvement under constraints?",
            "type": "relevance_gate",
            "target_dimension": "relevance",
            "reasoning_action": "Answer the question directly with one concrete example and the result.",
            "context_note": "Grounded in the original system-performance question.",
            "stage": 1,
            "grounding_score": 0.95,
        }
        evaluation["evaluation_confidence"] = {"relevance": 0.0, "grounding": 0.0, "completeness": 0.0, "overall": 0.0, "conflict": False}
        evaluation["grounding_score"] = 0.0
        return evaluation

    def _grounding_score(self, evaluation: Mapping[str, Any]) -> float:
        warning = evaluation.get("validation_warning", {}) if isinstance(evaluation.get("validation_warning"), Mapping) else {}
        trust = evaluation.get("trust", {}) if isinstance(evaluation.get("trust"), Mapping) else {}
        value = warning.get("score_confidence", trust.get("score_confidence", 0.0))
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _evaluation_confidence(self, evaluation: Mapping[str, Any], relevance_state: Mapping[str, Any], grounding_score: float) -> dict[str, Any]:
        context = evaluation.get("evaluation_context", {}) if isinstance(evaluation.get("evaluation_context"), Mapping) else {}
        coverage_values = [1.0 if context.get(key) else 0.0 for key in ("has_metrics", "has_structure", "has_reasoning", "has_tradeoffs", "has_alternatives")]
        completeness = round(sum(coverage_values) / len(coverage_values), 2) if coverage_values else 0.0
        relevance = round(float(relevance_state.get("confidence", 0.0)), 2)
        grounding = round(grounding_score, 2)
        overall = round((relevance + grounding + completeness) / 3, 2)
        return {
            "relevance": relevance,
            "grounding": grounding,
            "completeness": completeness,
            "overall": overall,
            "conflict": bool(relevance_state.get("conflict")),
        }

    def _ground_follow_up(self, evaluation: Mapping[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        follow_up = dict(evaluation.get("follow_up", {})) if isinstance(evaluation.get("follow_up"), Mapping) else {}
        feedback = dict(evaluation.get("feedback", {})) if isinstance(evaluation.get("feedback"), Mapping) else {}
        validation_warning = dict(evaluation.get("validation_warning", {})) if isinstance(evaluation.get("validation_warning"), Mapping) else {}
        issues = [str(item).strip() for item in feedback.get("key_issues", []) if str(item).strip()]
        improvements = [str(item).strip() for item in feedback.get("improvements", []) if str(item).strip()]
        issue_text = " ".join((issues + improvements)).lower()
        top_issue = issues[0] if issues else improvements[0] if improvements else ""
        stage = min(len([item for item in evaluation.get("future_session_memory", []) if isinstance(item, Mapping)]) + 1, 3)
        if relevance_state.get("combined_verdict") is False:
            return {
                "question": "Can you describe a real example where you improved system performance under constraints with measurable results?",
                "type": "relevance_gate",
                "target_dimension": "relevance",
                "reasoning_action": "Answer the question directly with one concrete example and the result.",
                "context_note": "Grounded in the original system-performance question.",
                "stage": stage,
                "grounding_score": 0.95,
            }
        if follow_up.get("question") and self._follow_up_is_grounded(follow_up, issue_text):
            follow_up["stage"] = stage
            follow_up["grounding_score"] = 0.8
            if not follow_up.get("reasoning_action"):
                follow_up["reasoning_action"] = self._reasoning_action(str(validation_warning.get("reasoning_depth", "implicit")))
            return follow_up
        weakest_key = min(_DIMENSIONS, key=lambda key: int(evaluation.get("scores", {}).get(key, 0)))
        weakest_label = weakest_key
        issue_tail = f"to address {top_issue.lower()}" if top_issue else ""
        if "metric" in issue_text or "impact" in issue_text:
            question = f"How would you prove the impact of this change with one concrete metric {issue_tail}?".strip()
            target_dimension = "specificity"
            context = "metrics and impact"
        elif "trade-off" in issue_text or "alternative" in issue_text:
            question = f"What alternative did you reject, and what trade-off made this choice better {issue_tail}?".strip()
            target_dimension = "problem_solving_approach"
            context = "trade-offs and alternatives"
        elif "structure" in issue_text or "star" in issue_text:
            question = f"How would you reshape this answer into a clearer Situation-Task-Action-Result flow {issue_tail}?".strip()
            target_dimension = "structure"
            context = "structure and flow"
        else:
            question = (
                f"How would you explain why this was the right trade-off compared with one alternative {issue_tail}?"
                if weakest_key == "problem_solving_approach"
                else f"What would you change if you had to strengthen the {weakest_label} part of this answer {issue_tail}?"
            )
            target_dimension = weakest_key
            context = weakest_label
        follow_up.update(
            {
                "question": question,
                "type": "depth_probe",
                "target_dimension": target_dimension,
                "reasoning_action": self._reasoning_action(str(validation_warning.get("reasoning_depth", "implicit"))),
                "context_note": f"Grounded in {context}.",
                "stage": stage,
                "grounding_score": 0.88,
            }
        )
        return follow_up

    def _degraded_evaluation(self, question: str, answer: str, reason: str, relevance_state: Mapping[str, Any]) -> dict[str, Any]:
        input_state = self.validate_input(question, answer)
        scores = {key: 5 for key in _DIMENSIONS}
        fallback_state = build_fallback_review_state(scores, topic_match=True, relevance_gate_applied=False, overall_decision="borderline pass")
        fallback_state["trust"]["score_confidence"] = 0.3
        fallback_state["trust"]["decision_confidence"] = "low"
        fallback_state["trust"]["reason"] = "Evaluation degraded due to model instability."
        fallback_state["validation_warning"]["score_confidence"] = 0.3
        fallback_state["validation_warning"]["trust_level"] = "low"
        fallback_state["validation_warning"]["reasoning_depth"] = "developing"
        fallback_state["validation_warning"]["interpretation"] = "Evaluation degraded due to model instability."
        fallback_state["overall_decision_detail"]["trust_level"] = "low"
        fallback_state["overall_decision_detail"]["score_confidence"] = 0.3
        fallback_state["overall_decision_detail"]["decision_confidence"] = "low"
        fallback_state["overall_decision_detail"]["reason"] = "Evaluation degraded due to model instability."
        evaluation = {
            "question": question,
            "answer": answer,
            "reference_answer": "",
            "semantic_similarity_score": 0.0,
            "overall_decision": "borderline pass",
            "overall_summary": "Evaluation degraded due to model instability.",
            "scores": scores,
            "labels": {key: "" for key in _DIMENSIONS},
            "feedback": {
                "summary": "Evaluation degraded due to model instability.",
                "strengths": [],
                "key_issues": ["The evaluator could not complete a reliable pass across the free-model chain."],
                "improvements": ["Retry the evaluation shortly so the rubric can be recomputed."],
            },
            "reasoning": {
                "clarity": "The answer could not be scored reliably because the model chain was unstable.",
                "alternative_approaches": "Not assessed because the evaluator fell back to a safe default.",
                "trade_off_awareness": "Not assessed because the evaluator fell back to a safe default.",
                "evidence": "No stable model output was available to extract evidence from.",
            },
            "follow_up": {
                "question": "Retry the evaluation once the model chain is stable, then review the detailed rubric again.",
                "type": "degraded_fallback",
                "target_dimension": "relevance",
                "reasoning_action": "Use the fallback result only as a temporary placeholder.",
                "context_note": "Grounded in model instability, not answer quality.",
                "stage": 1,
                "grounding_score": 0.3,
            },
            "topic_match": bool(relevance_state.get("combined_verdict", True)),
            "relevance_gate_applied": False,
            "failure_type": "low_evidence",
            "evaluation_context": {
                "evaluation_version": "fallback-eval-v1",
                "evaluation_trace": ["version:fallback-eval-v1", "evaluation_chain_degraded", f"reason:{reason or 'unknown'}"],
                "has_metrics": False,
                "metrics": [],
                "has_structure": False,
                "has_reasoning": False,
                "has_tradeoffs": False,
                "has_alternatives": False,
                "confidence": {"metrics": 0.0, "structure": 0.0, "reasoning": 0.0, "tradeoffs": 0.0, "alternatives": 0.0},
                "contradiction_flags": [],
                "anomaly_flags": ["model_instability"],
                "numeric_signals": [],
                "impact_strength": "moderate",
                "topic_match": True,
            },
            "trust": fallback_state["trust"],
            "validation_warning": fallback_state["validation_warning"],
            "overall_decision_detail": fallback_state["overall_decision_detail"],
            "evaluation_confidence": {"relevance": 0.5, "grounding": 0.3, "completeness": 0.2, "overall": 0.3, "conflict": False},
            "grounding_score": 0.3,
            "normalisation": build_normalisation(scores),
            "normalised_score_detail": "",
            "evaluation_summary": {
                "confidence_label": "Low",
                "grounding_label": "Weak",
                "failure_type": "low_evidence",
                "reason": "Evaluation degraded due to model instability.",
                "decision": "borderline pass",
            },
            "evaluation_pipeline": {
                "stages": [
                    {"name": "input_validator", "status": "ok", "issues": list(input_state.get("issues", []))},
                    {"name": "pre_classifier", "status": "ok", "match": bool(relevance_state["preclassification"]["match"]), "confidence": relevance_state["preclassification"].get("confidence", "low"), "reason": relevance_state["preclassification"].get("reason", "")},
                    {"name": "semantic_verifier", "status": "skipped", "match": bool(relevance_state["combined_verdict"]), "conflict": bool(relevance_state["conflict"])},
                    {"name": "evaluation_engine", "status": "failed"},
                    {"name": "grounding_validator", "status": "skipped", "grounding_score": 0.3},
                    {"name": "rule_enforcer", "status": "applied"},
                    {"name": "trust_calculator", "status": "ok", "evaluation_confidence": {"relevance": 0.5, "grounding": 0.3, "completeness": 0.2, "overall": 0.3, "conflict": False}},
                    {"name": "follow_up_generator", "status": "ok", "grounding_score": 0.3},
                    {"name": "output_formatter", "status": "ok"},
                ],
                "classifier_conflict": bool(relevance_state["conflict"]),
                "input_issues": list(input_state.get("issues", [])),
                "grounded": False,
                "model_instability": True,
                "note": "Evaluation degraded due to model instability.",
            },
        }
        evaluation["normalised_score_detail"] = evaluation["normalisation"].get("detail", "") if isinstance(evaluation["normalisation"], dict) else ""
        return evaluation

    def _follow_up_is_grounded(self, follow_up: Mapping[str, Any], issue_text: str) -> bool:
        question = str(follow_up.get("question", "")).lower()
        target_dimension = str(follow_up.get("target_dimension", "")).strip()
        if not question:
            return False
        if target_dimension == "relevance":
            return "system performance" in question or "measurable" in question
        if target_dimension == "specificity":
            return any(token in question for token in ("metric", "impact", "measure"))
        if target_dimension == "problem_solving_approach":
            return any(token in question for token in ("trade-off", "alternative", "tradeoff"))
        if target_dimension == "structure":
            return any(token in question for token in ("structure", "situation", "task", "action", "result", "star"))
        return any(token in question for token in issue_text.split()[:5])

    def _reasoning_action(self, depth: str) -> str:
        return {
            "none": "State why you chose this answer and name one concrete decision.",
            "implicit": "Explain why this approach was better than a simpler alternative.",
            "developing": "Add one rejected option and one trade-off you accepted.",
            "explicit": "Connect the decision to constraints, evidence, and the result.",
            "deep": "Summarise the trade-off and the impact in one crisp closing sentence.",
        }.get(depth, "Turn the reasoning into one explicit decision and one trade-off.")

    def _attach_pipeline(self, result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any], grounded: bool) -> dict[str, Any]:
        evaluation = dict(result)
        evaluation["question"] = input_state["question"]
        evaluation["answer"] = input_state["answer"]
        evaluation_context = dict(evaluation.get("evaluation_context", {}))
        grounding_score = self._grounding_score(evaluation)
        evaluation["grounding_score"] = grounding_score
        evaluation["evaluation_confidence"] = self._evaluation_confidence(evaluation, relevance_state, grounding_score)
        evaluation["failure_type"] = evaluation.get(
            "failure_type",
            classify_failure_type(evaluation, evaluation_context, grounding_score, evaluation["evaluation_confidence"]),
        )
        evaluation = apply_decision_adjustments(evaluation, evaluation["evaluation_confidence"], grounding_score)
        evaluation["evaluation_summary"] = evaluation.get(
            "evaluation_summary",
            build_evaluation_summary(evaluation, evaluation["failure_type"], evaluation["evaluation_confidence"], grounding_score),
        )
        evaluation["evaluation_pipeline"] = {
            "stages": [
                {"name": "input_validator", "status": "ok", "issues": list(input_state.get("issues", []))},
                {
                    "name": "pre_classifier",
                    "status": "ok",
                    "match": bool(relevance_state["preclassification"]["match"]),
                    "confidence": relevance_state["preclassification"].get("confidence", "low"),
                    "reason": relevance_state["preclassification"].get("reason", ""),
                },
                {
                    "name": "semantic_verifier",
                    "status": "ok" if grounded else "skipped",
                    "match": bool(relevance_state["combined_verdict"]),
                    "conflict": bool(relevance_state["conflict"]),
                },
                {"name": "evaluation_engine", "status": "ok" if grounded else "skipped"},
                {"name": "grounding_validator", "status": "ok" if grounded else "skipped", "grounding_score": evaluation.get("grounding_score", 0.0)},
                {"name": "rule_enforcer", "status": "ok" if grounded else "applied"},
                {"name": "trust_calculator", "status": "ok", "evaluation_confidence": evaluation.get("evaluation_confidence", {})},
                {"name": "follow_up_generator", "status": "ok", "grounding_score": evaluation.get("follow_up", {}).get("grounding_score", 0.0)},
                {"name": "output_formatter", "status": "ok"},
            ],
            "classifier_conflict": bool(relevance_state["conflict"]),
            "input_issues": list(input_state.get("issues", [])),
            "grounded": grounded,
        }
        return evaluation
