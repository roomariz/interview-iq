import pytest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload


QUESTION = "Describe a time you improved system performance under constraints."


def _scores(relevance, structure, specificity, communication, problem_solving_approach):
    return {
        "technical_accuracy": specificity,
        "clarity": communication,
        "structure": structure,
        "relevance": relevance,
        "problem_solving_approach": problem_solving_approach,
        "specificity": specificity,
        "communication": communication,
    }


def _payload(scores, key_issues=None, improvements=None, strengths=None, summary="Summary."):
    return {
        "evidence": {"metrics": [], "actions": [], "reasoning": ""},
        "scores": scores,
        "labels": {key: "" for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")},
        "feedback": {"summary": summary, "strengths": strengths or [], "key_issues": key_issues or [], "improvements": improvements or []},
        "reasoning": {"clarity": "", "alternative_approaches": "", "trade_off_awareness": "", "evidence": ""},
        "follow_up": {"question": "", "type": "", "target_dimension": ""},
        "example_answer": {},
        "strengths": strengths or [],
        "improvement_areas": improvements or [],
        "overall_summary": summary,
        "evaluation_version": "trust-v4",
        "evaluation_trace": ["version:trust-v4"],
        "impact_strength": "weak",
    }


def _evaluate(answer, context, payload, relevant=True):
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=relevant), patch(
        "interview_app_backend.services.evaluation_service.get_openrouter_client", return_value=object()
    ), patch(
        "interview_app_backend.services.evaluation_service.call_llm", return_value="{}"
    ), patch(
        "interview_app_backend.services.evaluation_service.generate_reference_answer", return_value="Reference answer."
    ), patch("interview_app_backend.services.evaluation_service.calculate_semantic_similarity", return_value=0.88), patch(
        "interview_app_backend.services.evaluation_service.extract_evidence_context", return_value=context
    ), patch("interview_app_backend.services.evaluation_service.parse_json_response", return_value=payload):
        return evaluate_submission(QUESTION, answer)


class TestNegativeHallucination:
    def test_feedback_does_not_mention_caching_when_not_in_answer(self):
        payload = _payload(
            _scores(6, 5, 5, 6, 4),
            key_issues=["Could provide more specific details"],
            improvements=["Consider adding concrete metrics"],
            summary="Answer is relevant but lacks specificity."
        )
        result = _evaluate(
            "I improved database query performance by optimising indexes.",
            {"has_metrics": False, "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.2, "structure": 0.5, "reasoning": 0.2, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        assert "caching" not in all_feedback_text
        assert "cache" not in all_feedback_text

    def test_feedback_does_not_mention_denormalisation_when_not_in_answer(self):
        payload = _payload(
            _scores(7, 6, 6, 7, 5),
            key_issues=["Could discuss alternative approaches"],
            improvements=["Consider mentioning one alternative you evaluated"],
            summary="Good answer with some evidence."
        )
        result = _evaluate(
            "I reduced API response time by optimising the business logic and using efficient data structures.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.7, "structure": 0.6, "reasoning": 0.5, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "moderate"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        assert "denormalisation" not in all_feedback_text
        assert "denormalize" not in all_feedback_text

    def test_feedback_does_not_mention_async_messaging_when_not_in_answer(self):
        payload = _payload(
            _scores(5, 5, 4, 5, 4),
            key_issues=["Outcome is vague"],
            improvements=["Specify the measurable impact"],
            summary="Answer lacks concrete results."
        )
        result = _evaluate(
            "I worked on improving the backend service.",
            {"has_metrics": False, "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.2, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        assert "async" not in all_feedback_text
        assert "kafka" not in all_feedback_text
        assert "rabbitmq" not in all_feedback_text
        assert "message queue" not in all_feedback_text

    def test_feedback_does_not_mention_sharding_when_not_in_answer(self):
        payload = _payload(
            _scores(6, 6, 5, 6, 5),
            key_issues=["Could mention trade-offs"],
            improvements=["Discuss the trade-offs you made"],
            summary="Solid answer but could be more thorough."
        )
        result = _evaluate(
            "I improved the system by refactoring the code and adding better error handling.",
            {"has_metrics": False, "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.2, "structure": 0.5, "reasoning": 0.2, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        assert "sharding" not in all_feedback_text
        assert "partition" not in all_feedback_text

    def test_feedback_can_mention_techniques_actually_in_answer(self):
        payload = _payload(
            _scores(8, 7, 8, 7, 6),
            key_issues=["Could discuss alternatives"],
            strengths=["Good use of caching to reduce latency"],
            improvements=["Mention alternative approaches considered"],
            summary="Strong answer with specific technique."
        )
        result = _evaluate(
            "I improved system performance by implementing Redis caching for frequently accessed data.",
            {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.7, "reasoning": 0.6, "tradeoffs": 0.3, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "moderate"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        assert "caching" in all_feedback_text or "cache" in all_feedback_text

    def test_feedback_does_not_suggest_specific_tech_not_mentioned(self):
        payload = _payload(
            _scores(5, 4, 4, 5, 4),
            key_issues=["Results are unclear"],
            improvements=["Quantify the improvement"],
            summary="Vague answer needs specifics."
        )
        result = _evaluate(
            "I made the database faster.",
            {"has_metrics": False, "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.1, "reasoning": 0.1, "tradeoffs": 0.1, "alternatives": 0.1}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"},
            payload
        )
        view = normalise_feedback_payload(result)
        all_feedback_text = " ".join(view.get("improvements", []) + view.get("key_issues", []) + view.get("strengths", [])).lower()

        specific_technologies = ["postgres", "mysql", "mongodb", "redis", "elasticsearch", "kubernetes", "docker"]
        for tech in specific_technologies:
            assert tech not in all_feedback_text