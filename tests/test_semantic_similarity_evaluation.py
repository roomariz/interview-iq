import unittest
from unittest.mock import patch

import streamlit as st

from interview_app_backend.llm.prompts.interview import build_reference_answer_prompt, build_semantic_similarity_prompt
from interview_app_backend.services.evaluation_service import evaluate_answer, evaluate_submission
from interview_app_frontend.state.session_manager import submit_answer


class TestSemanticSimilarityEvaluation(unittest.TestCase):
    def setUp(self) -> None:
        st.session_state.clear()

    def test_prompt_builders_include_comparison_context(self) -> None:
        reference_prompt = build_reference_answer_prompt("Explain a caching strategy.")
        similarity_prompt = build_semantic_similarity_prompt("Use caching to reduce repeated work.", "I cached repeated work.")

        self.assertIn("Explain a caching strategy.", reference_prompt)
        self.assertIn("Reference answer:", similarity_prompt)
        self.assertIn("User answer:", similarity_prompt)

    def test_evaluate_answer_includes_reference_context_in_request(self) -> None:
        payload = (
            '{"evidence":{"metrics":["90%"],"actions":["cached repeated work"],"reasoning":"Chose the simpler fix"},'
            '"scores":{"technical_accuracy":9,"clarity":8,"structure":7,"relevance":6,"problem_solving_approach":5},'
            '"strengths":["Clear answer"],"improvement_areas":["Add examples"],"overall_summary":"Strong response."}'
        )

        with patch(
            "interview_app_backend.services.evaluation_service.extract_evidence_context",
            return_value={
                "has_metrics": True,
                "metric_count": 1,
                "has_structure": True,
                "has_reasoning": True,
                "has_tradeoffs": False,
                "has_alternatives": False,
                "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.2, "alternatives": 0.2},
                "contradiction_flags": [],
                "anomaly_flags": [],
                "numeric_signals": ["90%"],
                "evaluation_version": "trust-v4",
                "evaluation_trace": ["version:trust-v4", "impact_strength:strong", "reasoning_depth:developing"],
                "impact_strength": "strong",
            },
        ), patch("interview_app_backend.services.evaluation_service.get_openrouter_client") as mock_client, patch(
            "interview_app_backend.services.evaluation_service.call_llm",
            return_value=payload,
        ) as mock_call, patch(
            "interview_app_backend.services.evaluation_service.parse_json_response",
            return_value={
                "evidence": {
                    "metrics": ["90%"],
                    "actions": ["cached repeated work"],
                    "reasoning": "Chose the simpler fix",
                },
                "technical_accuracy": 9,
                "clarity": 8,
                "structure": 7,
                "relevance": 6,
                "problem_solving_approach": 5,
                "strengths": ["Clear answer"],
                "improvement_areas": ["Add examples"],
                "overall_summary": "Strong response.",
            },
        ), patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True):
            evaluate_answer(
                "Question text.",
                "User answer.",
                reference_answer="Reference answer.",
                semantic_similarity_score=0.82,
            )

        prompt = mock_call.call_args.args[0]
        self.assertIn("Reference answer:", prompt)
        self.assertIn("Semantic similarity score: 0.82", prompt)
        self.assertIn("Question:\nQuestion text.", prompt)
        self.assertIn("JSON schema:", prompt)
        self.assertIn("Evaluation context:", prompt)
        self.assertIn('"has_metrics": true', prompt.lower())
        self.assertIn("Scoring rules:", prompt)
        self.assertIn("Specificity rubric:", prompt)
        self.assertIn("Structure rubric:", prompt)
        self.assertIn("Problem-solving rubric:", prompt)
        self.assertIn("Similarity (supporting only):", prompt)
        self.assertIn("Cross-check key issues and improvements against the extracted evidence", prompt)
        self.assertIn('"confidence"', prompt)
        self.assertIn('"anomaly_flags"', prompt)
        self.assertIn("Return JSON only.", prompt)
        mock_client.assert_called_once()

    def test_evaluate_answer_preserves_metrics_and_rewrites_generic_feedback(self) -> None:
        answer = (
            "Challenge: the API was slow. Approach: I profiled hot paths, cached repeated work, and tuned the query. "
            "Results: latency reduced from 400ms to 90ms, throughput increased by 2.5x, CPU reduced by 40%, "
            "and error rates reduced by 30% with no new infrastructure budget."
        )
        bad_payload = (
            '{"evidence":{"metrics":["400ms","90ms","2.5x","40%"],"actions":["profiled hot paths"],"reasoning":"Chose a smaller change to reduce risk"},'
            '"scores":{"technical_accuracy":9,"clarity":8,"structure":7,"relevance":9,"problem_solving_approach":6,"specificity":8,"communication":8},'
            '"labels":{"relevance":"Addresses the question directly","structure":"Lacks structure","specificity":"Lacks measurable outcomes",'
            '"communication":"Clear","problem_solving_approach":"Solution is correct, but reasoning is implicit"},'
            '"feedback":{"summary":"Strong response.","strengths":["Clear answer"],"key_issues":["Missing specific metrics for improvement","Lacks measurable outcomes"],'
            '"improvements":["Add quantifiable results such as latency reduction or throughput gains","Explain technical decisions and trade-offs",'
            '"Discuss alternative approaches and why they were rejected"]},'
            '"overall_summary":"Strong response."}'
        )

        with patch(
            "interview_app_backend.services.evaluation_service.extract_evidence_context",
            return_value={
                "has_metrics": True,
                "metric_count": 4,
                "has_structure": True,
                "has_reasoning": True,
                "has_tradeoffs": True,
                "has_alternatives": False,
                "confidence": {"metrics": 0.88, "structure": 0.91, "reasoning": 0.9, "tradeoffs": 0.7, "alternatives": 0.3},
                "contradiction_flags": ["metrics_contradiction"],
                "anomaly_flags": ["ambiguous_metrics"],
                "numeric_signals": ["400ms", "90ms", "2.5x", "40%"],
                "evaluation_version": "trust-v4",
                "evaluation_trace": ["version:trust-v4", "impact_strength:strong", "reasoning_depth:developing"],
                "impact_strength": "strong",
            },
        ), patch("interview_app_backend.services.evaluation_service.get_openrouter_client") as mock_client, patch(
            "interview_app_backend.services.evaluation_service.call_llm",
            return_value=bad_payload,
        ) as mock_call, patch(
            "interview_app_backend.services.evaluation_service.parse_json_response",
            return_value={
                "evidence": {"metrics": ["400ms", "90ms", "2.5x", "40%"], "actions": ["profiled hot paths"], "reasoning": "Chose a smaller change to reduce risk"},
                "scores": {
                    "technical_accuracy": 9,
                    "clarity": 8,
                    "structure": 7,
                    "relevance": 9,
                    "problem_solving_approach": 6,
                    "specificity": 8,
                    "communication": 8,
                },
                "labels": {
                    "relevance": "Addresses the question directly",
                    "structure": "Lacks structure",
                    "specificity": "Lacks measurable outcomes",
                    "communication": "Clear",
                    "problem_solving_approach": "Solution is correct, but reasoning is implicit",
                },
                "feedback": {
                    "summary": "Strong response.",
                    "strengths": ["Clear answer"],
                    "key_issues": ["Missing specific metrics for improvement", "Lacks measurable outcomes"],
                    "improvements": [
                        "Add quantifiable results such as latency reduction or throughput gains",
                        "Explain technical decisions and trade-offs",
                        "Discuss alternative approaches and why they were rejected",
                    ],
                },
                "overall_summary": "Strong response.",
            },
        ), patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True), self.assertLogs("interview_app_backend.services.evaluation_rules", level="WARNING") as captured:
            result = evaluate_answer("Describe a time you improved system performance under constraints.", answer)

        prompt = mock_call.call_args.args[0]
        self.assertIn("Evaluation context:", prompt)
        self.assertIn('"has_metrics": true', prompt.lower())
        self.assertIn("Metrics are present, but could be tied more clearly to business or user impact.", prompt)
        self.assertGreaterEqual(result["scores"]["specificity"], 8)
        self.assertGreaterEqual(result["scores"]["structure"], 7)
        self.assertGreaterEqual(result["scores"]["problem_solving_approach"], 6)
        self.assertEqual(result["overall_decision"], "pass")
        self.assertEqual(result["evaluation_context"]["metric_count"], 4)
        self.assertEqual(result["evaluation_context"]["confidence"]["metrics"], 0.88)
        self.assertIn("metrics_contradiction", result["validation_warning"]["contradiction_flags"])
        self.assertEqual(result["validation_warning"]["severity"], "high")
        self.assertEqual(result["validation_warning"]["trust_level"], "low")
        self.assertIn("grouped_anomaly_flags", result["validation_warning"])
        self.assertIn("flags affect interpretation", result["validation_warning"]["interpretation"])
        self.assertIn("validation", result["validation_warning"])
        self.assertIn("trust", result["validation_warning"])
        self.assertIn("reasoning", result["validation_warning"])
        self.assertEqual(result["evaluation_version"], "trust-v4")
        self.assertTrue(result["evaluation_trace"])
        self.assertGreaterEqual(result["score_confidence"], 0)
        self.assertIn("ambiguous_metrics", result["validation_warning"]["anomaly_flags"])
        self.assertNotIn("Missing specific metrics for improvement", " | ".join(result["feedback"]["key_issues"]))
        self.assertIn("decision-making behind each technical choice", " | ".join(result["feedback"]["key_issues"]))
        self.assertIn("Keep the existing metrics", " | ".join(result["feedback"]["improvements"]))
        self.assertTrue(result.get("validation_warnings"))
        self.assertTrue(any("normalised" in message.lower() for message in captured.output))
        mock_client.assert_called_once()

    def test_submit_answer_stores_reference_answer_and_similarity_score(self) -> None:
        st.session_state.answer = "This answer explains the challenge, approach, and measurable result clearly."
        st.session_state.answers = []
        st.session_state.answer_submit_error = ""
        st.session_state.current_question = "Describe a time you improved system performance under constraints."

        with patch(
            "interview_app_frontend.state.session_manager.evaluate_submission",
            return_value={
                "question": st.session_state.current_question,
                "answer": st.session_state.answer.strip(),
                "reference_answer": "Model answer.",
                "semantic_similarity_score": 0.91,
            },
        ):
            submit_answer()

        self.assertEqual(st.session_state.reference_answer, "Model answer.")
        self.assertEqual(st.session_state.semantic_similarity_score, 0.91)
        self.assertEqual(st.session_state.feedback["reference_answer"], "Model answer.")
        self.assertEqual(st.session_state.feedback["semantic_similarity_score"], 0.91)

    def test_evaluate_submission_combines_generated_fields(self) -> None:
        with patch(
            "interview_app_backend.services.evaluation_service.generate_reference_answer",
            return_value="Reference answer.",
        ), patch(
            "interview_app_backend.services.evaluation_service.calculate_semantic_similarity",
            return_value=0.87,
        ), patch(
            "interview_app_backend.services.evaluation_service.evaluate_answer",
            return_value={
                "technical_accuracy": 9,
                "clarity": 8,
                "structure": 7,
                "relevance": 6,
                "strengths": ["Clear answer"],
                "improvement_areas": ["Add examples"],
                "overall_summary": "Strong response.",
                "answer": "User answer.",
            },
        ), patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True):
            result = evaluate_submission("Question?", "User answer.")

        self.assertEqual(result["reference_answer"], "Reference answer.")
        self.assertEqual(result["semantic_similarity_score"], 0.87)
        self.assertEqual(result["question"], "Question?")


if __name__ == "__main__":
    unittest.main()
