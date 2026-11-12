import importlib
import os
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path


class TestEnvironmentLoading(unittest.TestCase):
    def test_settings_reads_openrouter_api_key_from_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=True), unittest.mock.patch(
                "pathlib.Path.resolve"
            ) as mock_resolve:
                mock_resolve.return_value = temp_root / "config" / "settings.py"
                settings = importlib.import_module("config.settings")
                settings = importlib.reload(settings)

        self.assertEqual(settings.OPENROUTER_API_KEY, "env-key")

    def test_settings_defaults_to_empty_string_when_environment_variable_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with patch.dict(os.environ, {}, clear=True), unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = temp_root / "config" / "settings.py"
                settings = importlib.import_module("config.settings")
                settings = importlib.reload(settings)

        self.assertEqual(settings.OPENROUTER_API_KEY, "")
        self.assertEqual(settings.GOOGLE_API_KEY, "")
        self.assertEqual(settings.XAI_API_KEY, "")

    def test_settings_loads_openrouter_api_key_from_repo_env_file(self):
        settings = importlib.import_module("config.settings")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            (temp_root / ".env").write_text("OPENROUTER_API_KEY=file-key\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True), unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = temp_root / "config" / "settings.py"
                settings = importlib.reload(settings)

        self.assertEqual(settings.OPENROUTER_API_KEY, "file-key")

    def test_settings_prefers_repo_env_model_name_over_shell_variable(self):
        settings = importlib.import_module("config.settings")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            (temp_root / ".env").write_text("MODEL_NAME=file-model\n", encoding="utf-8")
            with patch.dict(os.environ, {"MODEL_NAME": "shell-model", "IS_FREE_MODE": "false"}, clear=True), unittest.mock.patch(
                "pathlib.Path.resolve"
            ) as mock_resolve:
                mock_resolve.return_value = temp_root / "config" / "settings.py"
                settings = importlib.reload(settings)

        self.assertEqual(settings.MODEL_NAME, "file-model")

    def test_settings_defaults_to_free_model_when_free_mode_is_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with patch.dict(os.environ, {}, clear=True), unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = temp_root / "config" / "settings.py"
                settings = importlib.import_module("config.settings")
                settings = importlib.reload(settings)

        self.assertTrue(settings.IS_FREE_MODE)
        self.assertEqual(settings.DEFAULT_MODEL, "google/gemma-4-31b-it:free")
        self.assertEqual(settings.MODEL_NAME, "google/gemma-4-31b-it:free")

    def test_settings_exposes_free_models_list(self):
        settings = importlib.import_module("config.settings")

        self.assertEqual(
            settings.FREE_MODELS,
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
            ],
        )
        self.assertEqual(
            settings.FREE_EVAL_MODELS,
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
            ],
        )
        self.assertEqual(
            settings.QUESTION_GENERATION_FALLBACK_CHAIN,
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        )
        self.assertEqual(
            settings.FALLBACK_CHAIN,
            [
                "google/gemma-4-31b-it:free",
                "google/gemma-3-12b-it:free",
                "openai/gpt-5-nano",
            ],
        )


if __name__ == "__main__":
    unittest.main()
