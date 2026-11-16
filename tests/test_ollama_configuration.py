import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.py"


def load_settings(environment, file_values=None):
    with patch.dict("os.environ", environment, clear=True), patch("dotenv.load_dotenv"), patch(
        "dotenv.dotenv_values", return_value=file_values or {}
    ):
        return runpy.run_path(str(SETTINGS_PATH))


def test_default_preserves_openrouter_models_and_ranking():
    config = load_settings({})
    assert config["LLM_PROVIDER"] == "open-router"
    assert config["MODEL_NAME"] == config["OPENROUTER_MODEL_NAME"] == "google/gemma-4-31b-it:free"
    assert config["OLLAMA_FALLBACK_TO_OPENROUTER"] is False
    assert config["FALLBACK_CHAIN"] == ["google/gemma-4-31b-it:free", "google/gemma-3-12b-it:free", "openai/gpt-5-nano"]


def test_cloud_configuration_does_not_override_openrouter_model():
    config = load_settings({
        "LLM_PROVIDER": "ollama", "OLLAMA_API_KEY": "test-key",
        "OLLAMA_MODEL": "gemma4:cloud", "OLLAMA_HOST": "https://ollama.com",
        "IS_FREE_MODE": "false", "MODEL_NAME": "existing/paid-model",
    })
    assert config["PRIMARY_PROVIDER"] == "ollama"
    assert config["MODEL_NAME"] == "gemma4:cloud"
    assert config["OPENROUTER_MODEL_NAME"] == "existing/paid-model"
    assert config["OLLAMA_API_KEY"] == "test-key"
    assert config["OLLAMA_HOST"] == "https://ollama.com"


def test_deployment_environment_overrides_file_for_new_settings():
    config = load_settings({"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "custom-model"}, {
        "LLM_PROVIDER": "openrouter", "OLLAMA_MODEL": "file-model", "OLLAMA_API_KEY": "file-key",
        "OLLAMA_FALLBACK_TO_OPENROUTER": "true",
    })
    assert config["LLM_PROVIDER"] == "ollama"
    assert config["OLLAMA_MODEL"] == "custom-model"
    assert config["OLLAMA_API_KEY"] == "file-key"
    assert config["OLLAMA_FALLBACK_TO_OPENROUTER"] is True


def test_provider_alias_and_unknown_provider():
    assert load_settings({"LLM_PROVIDER": "openrouter"})["LLM_PROVIDER"] == "open-router"
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        load_settings({"LLM_PROVIDER": "typo"})


@pytest.mark.parametrize("local_host", ["0.0.0.0:11434", "http://localhost:11434"])
def test_project_cloud_host_overrides_inherited_local_ollama_host(local_host):
    config = load_settings({"LLM_PROVIDER": "ollama", "OLLAMA_HOST": local_host}, {
        "OLLAMA_HOST": "https://ollama.com",
    })
    assert config["OLLAMA_HOST"] == "https://ollama.com"


def test_cloud_host_can_still_come_from_deployment_environment():
    config = load_settings({"LLM_PROVIDER": "ollama", "OLLAMA_HOST": "https://ollama.com"})
    assert config["OLLAMA_HOST"] == "https://ollama.com"


def test_project_ollama_key_overrides_a_different_inherited_key():
    config = load_settings({"LLM_PROVIDER": "ollama", "OLLAMA_API_KEY": "inherited-key"}, {
        "OLLAMA_API_KEY": "project-key",
    })
    assert config["OLLAMA_API_KEY"] == "project-key"


@pytest.mark.parametrize("file_key", [None, ""])
def test_ollama_key_supports_environment_only_deployments(file_key):
    config = load_settings({"LLM_PROVIDER": "ollama", "OLLAMA_API_KEY": "deployment-key"}, {
        "OLLAMA_API_KEY": file_key,
    })
    assert config["OLLAMA_API_KEY"] == "deployment-key"
