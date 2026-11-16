import unittest
from unittest.mock import patch


from interview_app_backend.llm.client import create_openrouter_client, get_openrouter_client
from interview_app_backend.llm.provider_clients import create_grok_client, get_grok_client


class TestClientConfiguration(unittest.TestCase):
    def test_create_openrouter_client_uses_openrouter_base_url(self):
        with patch("interview_app_backend.llm.client.OpenAI") as mock_openai:
            create_openrouter_client("test-key")

        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-OpenRouter-Title": "InterviewIQ",
            },
        )

    def test_call_llm_uses_configured_model_name(self):
        from interview_app_backend.llm import client as client_module

        response = unittest.mock.Mock(output_text="answer")
        mock_client = unittest.mock.Mock()
        mock_client.responses.create.return_value = response

        with patch.object(client_module, "MODEL_NAME", "google/gemma-4-31b-it:free"):
            result = client_module.call_llm("prompt", mock_client)

        self.assertEqual(result, "answer")
        mock_client.responses.create.assert_called_once_with(model="google/gemma-4-31b-it:free", input="prompt", timeout=60)

    def test_call_llm_logs_task_and_model(self):
        from interview_app_backend.llm import client as client_module

        response = unittest.mock.Mock(output_text="answer")
        mock_client = unittest.mock.Mock()
        mock_client.responses.create.return_value = response

        with patch.object(client_module, "MODEL_NAME", "google/gemma-4-31b-it:free"), patch("builtins.print") as mock_print, self.assertLogs(
            "interview_app_backend.llm.client",
            level="INFO",
        ) as logs:
            client_module.call_llm("prompt", mock_client, task="question_generation.cv_based")

        mock_print.assert_any_call("MODEL USED:", "google/gemma-4-31b-it:free")
        self.assertTrue(
            any(
                "status=success" in entry
                and "task=question_generation.cv_based" in entry
                and "model=google/gemma-4-31b-it:free" in entry
                for entry in logs.output
            )
        )

    def test_get_openrouter_client_uses_configured_api_key(self):
        with patch("interview_app_backend.llm.client.OPENROUTER_API_KEY", "configured-key"), patch(
            "interview_app_backend.llm.client.create_openrouter_client"
        ) as mock_create_client:
            sentinel = object()
            mock_create_client.return_value = sentinel

            result = get_openrouter_client()

        self.assertIs(result, sentinel)
        mock_create_client.assert_called_once_with("configured-key")

    def test_get_openrouter_client_raises_when_api_key_missing(self):
        with patch("interview_app_backend.llm.client.OPENROUTER_API_KEY", ""):
            with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY is not set"):
                get_openrouter_client()

    def test_create_grok_client_uses_xai_base_url(self):
        with patch("interview_app_backend.llm.provider_clients.OpenAI") as mock_openai:
            create_grok_client("test-key")

        mock_openai.assert_called_once_with(api_key="test-key", base_url="https://api.x.ai/v1")

    def test_get_grok_client_uses_configured_api_key(self):
        with patch("interview_app_backend.llm.provider_clients.XAI_API_KEY", "configured-key"), patch(
            "interview_app_backend.llm.provider_clients.create_grok_client"
        ) as mock_create_client:
            sentinel = object()
            mock_create_client.return_value = sentinel

            result = get_grok_client()

        self.assertIs(result, sentinel)
        mock_create_client.assert_called_once_with("configured-key")

    def test_get_grok_client_raises_when_api_key_missing(self):
        with patch("interview_app_backend.llm.provider_clients.XAI_API_KEY", ""):
            with self.assertRaisesRegex(ValueError, "XAI_API_KEY is not set"):
                get_grok_client()


if __name__ == "__main__":
    unittest.main()
