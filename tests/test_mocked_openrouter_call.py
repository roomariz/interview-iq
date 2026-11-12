import unittest
from unittest.mock import Mock, patch

from interview_app_backend.llm.client import call_llm, get_openrouter_client
from config.settings import MODEL_NAME


class TestMockedOpenRouterCall(unittest.TestCase):
    def test_call_llm_uses_mocked_openrouter_response(self):
        client = Mock()
        client.responses.create.return_value = Mock(output_text="mocked answer")

        result = call_llm("Explain dependency injection.", client)

        self.assertEqual(result, "mocked answer")
        client.responses.create.assert_called_once_with(
            model=MODEL_NAME,
            input="Explain dependency injection.",
        )

    def test_call_llm_accepts_plain_string_response(self):
        client = Mock()
        client.responses.create.return_value = "mocked answer"

        result = call_llm("Explain dependency injection.", client)

        self.assertEqual(result, "mocked answer")

    def test_call_llm_rejects_html_error_page_response(self):
        client = Mock()
        client.responses.create.return_value = "<!DOCTYPE html><html><body>OpenRouter error</body></html>"

        result = call_llm("Explain dependency injection.", client)

        self.assertEqual(result, "")

    def test_get_openrouter_client_returns_configured_client(self):
        with patch("interview_app_backend.llm.client.OPENROUTER_API_KEY", "test-key"), patch(
            "interview_app_backend.llm.client.OpenAI"
        ) as mock_openai:
            get_openrouter_client()

        mock_openai.assert_called_once_with(api_key="test-key", base_url="https://openrouter.ai/v1")


if __name__ == "__main__":
    unittest.main()
