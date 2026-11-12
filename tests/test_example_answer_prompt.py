import unittest
from unittest.mock import patch

from interview_app_backend.llm.prompts.interview import build_example_answer_prompt
from interview_app_backend.services.evaluation_service import EVALUATION_PROMPT, evaluate_answer, generate_example_answer


class TestExampleAnswerPrompt(unittest.TestCase):
    def test_build_example_answer_prompt_includes_rewrite_constraints(self):
        prompt = build_example_answer_prompt("  I improved latency by caching repeated work.  ")

        self.assertIn("Rewrite the answer to improve clarity, structure, and reasoning.", prompt)
        self.assertIn("Do NOT add new metrics, trade-offs, or experiences", prompt)
        self.assertIn("Original answer:\nI improved latency by caching repeated work.", prompt)
        self.assertNotIn("technical_accuracy", prompt)

    def test_generate_example_answer_uses_rewrite_prompt_and_strips_output(self):
        with patch("interview_app_backend.services.evaluation_service.get_openrouter_client") as mock_client, patch(
            "interview_app_backend.services.evaluation_service.call_llm",
            return_value="  Rewritten answer.  ",
        ) as mock_call:
            result = generate_example_answer("  I improved latency by caching repeated work.  ")

        self.assertEqual(result, "Rewritten answer.")
        mock_client.assert_called_once()
        prompt = mock_call.call_args.args[0]
        self.assertIn("Rewrite the answer to improve clarity, structure, and reasoning.", prompt)
        self.assertNotIn("technical_accuracy", prompt)

    def test_evaluate_answer_keeps_scoring_prompt_separate(self):
        scoring_payload = (
            '{"technical_accuracy":9,"clarity":8,"structure":7,"relevance":6,'
            '"strengths":["Clear answer"],"improvement_areas":["Add examples"],'
            '"overall_summary":"Strong response."}'
        )

        with patch("interview_app_backend.services.evaluation_service.get_openrouter_client") as mock_client, patch(
            "interview_app_backend.services.evaluation_service.call_llm",
            return_value=scoring_payload,
        ) as mock_call, patch(
            "interview_app_backend.services.evaluation_service.parse_json_response",
            return_value={
                "technical_accuracy": 9,
                "clarity": 8,
                "structure": 7,
                "relevance": 6,
                "strengths": ["Clear answer"],
                "improvement_areas": ["Add examples"],
                "overall_summary": "Strong response.",
            },
        ) as mock_parse:
            result = evaluate_answer(
                "Question text.",
                "I improved latency by caching repeated work.",
            )

        self.assertEqual(result["answer"], "I improved latency by caching repeated work.")
        mock_client.assert_called_once()
        prompt = mock_call.call_args.args[0]
        self.assertTrue(prompt.startswith(EVALUATION_PROMPT))
        self.assertIn("Question:\nQuestion text.", prompt)
        self.assertIn("Answer:\nI improved latency by caching repeated work.", prompt)
        self.assertNotIn("Rewrite the answer to improve clarity, structure, and reasoning.", prompt)
        mock_parse.assert_called_once_with(scoring_payload)


if __name__ == "__main__":
    unittest.main()
