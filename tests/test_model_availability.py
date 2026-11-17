import logging
import httpx
import pytest
from unittest.mock import patch, MagicMock

from interview_app_backend.llm.client import RateLimitError, call_llm, _extract_provider
from config.settings import FREE_MODELS, MODEL_NAME


LOGGER = logging.getLogger(__name__)


class TestModelProviderAvailability:

    @pytest.mark.parametrize("model", FREE_MODELS)
    def test_model_is_recognised(self, model):
        provider = _extract_provider(model)
        assert provider == "google", f"Unknown provider for {model}"

    def test_free_models_list_contains_expected(self):
        assert len(FREE_MODELS) == 2
        providers = [_extract_provider(m) for m in FREE_MODELS]
        assert "google" in providers


class TestModelFallbackLogic:

    def test_free_model_falls_back_to_next_free_model(self):
        mock_client = MagicMock()
        error_404 = Exception("Error code: 404 - {'error': {'message': 'No endpoints available'}")
        success_response = MagicMock(output_text='{"ok": true}')
        mock_client.responses.create.side_effect = [error_404, success_response]

        with patch("interview_app_backend.llm.client.MODEL_NAME", "google/gemma-4-31b-it:free"):
            with patch(
                "config.settings.FALLBACK_CHAIN",
                [
                    "google/gemma-4-31b-it:free",
                    "google/gemma-3-12b-it:free",
                    "openai/gpt-5-nano",
                ],
            ):
                assert call_llm("test", mock_client) == '{"ok": true}'
                assert mock_client.responses.create.call_count == 2

    def test_transient_free_model_retries_then_moves_on(self):
        mock_client = MagicMock()
        response = httpx.Response(429, request=httpx.Request("POST", "https://provider.example/responses"))
        errors = [
            RateLimitError("Error code: 429 - rate limited", response=response, body={"error": "rate limited"}),
            RateLimitError("Error code: 429 - rate limited", response=response, body={"error": "rate limited"}),
            RateLimitError("Error code: 429 - rate limited", response=response, body={"error": "rate limited"}),
            MagicMock(output_text='{"ok": true}'),
        ]
        mock_client.responses.create.side_effect = errors

        with patch("interview_app_backend.llm.client.MODEL_NAME", "google/gemma-4-31b-it:free"), patch(
            "config.settings.FALLBACK_CHAIN",
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        ), patch("interview_app_backend.llm.client.time.sleep", return_value=None):
            assert call_llm("test", mock_client) == '{"ok": true}'
            assert mock_client.responses.create.call_count == 4
            assert [call.kwargs["model"] for call in mock_client.responses.create.call_args_list] == [
                "google/gemma-4-31b-it:free",
                "google/gemma-4-31b-it:free",
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
            ]

    def test_permanent_bad_request_fails_fast(self):
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = [RuntimeError("Error code: 400 - bad request")]

        with patch("interview_app_backend.llm.client.MODEL_NAME", "google/gemma-4-31b-it:free"), patch(
            "config.settings.FALLBACK_CHAIN",
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        ):
            with pytest.raises(RuntimeError, match="400"):
                call_llm("test", mock_client)
            assert mock_client.responses.create.call_count == 1


def _test_which_models_work():
    print("\n" + "=" * 60)
    print("MODEL AVAILABILITY TEST")
    print("=" * 60)
    print(f"Configured MODEL_NAME: {MODEL_NAME}")
    print(f"Available models: {FREE_MODELS}")
    print("-" * 60)

    results = []
    for model in FREE_MODELS:
        provider = _extract_provider(model)
        results.append({"model": model, "provider": provider, "status": "N/A"})
        print(f"{provider:12} | {model:40} | {"N/A"}")

    print("-" * 60)
    return results


if __name__ == "__main__":
    _test_which_models_work()
