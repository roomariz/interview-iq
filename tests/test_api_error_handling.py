import unittest
from unittest.mock import Mock, patch

from interview_app_backend.llm.client import call_llm
from interview_app_backend.llm.client import APITimeoutError


class TestApiErrorHandling(unittest.TestCase):
    def test_call_llm_returns_response_text_on_success(self):
        response = Mock(output_text="answer")
        client = Mock()
        client.responses.create.return_value = response

        from interview_app_backend.llm import client as client_module

        with patch.object(client_module, "MODEL_NAME", "model-one"):
            result = call_llm("prompt", client)

        self.assertEqual(result, "answer")
        client.responses.create.assert_called_once_with(model="model-one", input="prompt", timeout=60)

    def test_call_llm_logs_empty_output(self):
        response = Mock(output_text="")
        client = Mock()
        client.responses.create.return_value = response

        from interview_app_backend.llm import client as client_module

        with patch.object(client_module, "MODEL_NAME", "model-one"), self.assertLogs(
            "interview_app_backend.llm.client",
            level="WARNING",
        ) as captured:
            result = call_llm("prompt", client)

        self.assertEqual(result, "")
        self.assertTrue(any("llm_empty_output" in line for line in captured.output))
        record = next(record for record in captured.records if record.getMessage() == "llm_empty_output")
        self.assertEqual(record.provider, "unknown")
        self.assertEqual(record.model, "model-one")
        self.assertEqual(record.raw_output_length, 0)

    def test_call_llm_moves_to_the_next_model_on_timeout(self):
        client = Mock()
        client.responses.create.side_effect = [
            APITimeoutError("timeout"),
            APITimeoutError("timeout"),
            APITimeoutError("timeout"),
            Mock(output_text="answer"),
        ]

        from interview_app_backend.llm import client as client_module

        with patch.object(client_module, "MODEL_NAME", "google/gemma-4-31b-it:free"), patch(
            "config.settings.FALLBACK_CHAIN",
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        ), patch.object(client_module.time, "sleep", return_value=None):
            result = call_llm("prompt", client)

        self.assertEqual(result, "answer")
        self.assertEqual(client.responses.create.call_count, 4)
        self.assertEqual(
            [call.kwargs["model"] for call in client.responses.create.call_args_list],
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-4-31b-it:free",
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
            ],
        )

    def test_call_llm_raises_after_all_models_fail(self):
        client = Mock()
        client.responses.create.side_effect = [
            RuntimeError("Error code: 404 - no endpoints available"),
            RuntimeError("Error code: 404 - no endpoints available"),
            RuntimeError("Error code: 404 - no endpoints available"),
            RuntimeError("Error code: 404 - no endpoints available"),
        ]

        from interview_app_backend.llm import client as client_module

        with patch.object(client_module, "MODEL_NAME", "google/gemma-4-31b-it:free"), patch(
            "config.settings.FALLBACK_CHAIN",
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        ):
            with self.assertRaisesRegex(RuntimeError, "We encountered an issue"):
                call_llm("prompt", client)

        self.assertEqual(client.responses.create.call_count, 3)


if __name__ == "__main__":
    unittest.main()
