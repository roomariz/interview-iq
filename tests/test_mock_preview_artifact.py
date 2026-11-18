"""Package and exercise exactly the backend source proposed for a new Preview."""

import os
from pathlib import Path
import subprocess
import sys
import pytest

from scripts.package_mock_preview import build


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    output = tmp_path_factory.mktemp("mock-preview") / "artifact"
    receipt = build(output)
    return output, receipt


def test_packaged_mock_is_isolated_and_completes_five_questions(artifact):
    output, receipt = artifact
    assert set(receipt["overlayFiles"]) == {"deployment/mock_preview.py", "deployment/mock_questions.py"}
    assert "mock_preview.py" in receipt["files"]
    assert "mock_questions.py" in receipt["files"]
    assert not any(name.startswith(("deployment/", "interview_app_frontend/", "tests/", "doc/", ".env"))
                   for name in receipt["files"])
    assert "from mock_preview import install" in (output / "api/index.py").read_text()
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ, PYTHONPATH=str(output))
    result = subprocess.run([sys.executable, str(root / "tests/mock_preview_artifact_check.py")],
                            cwd=output, env=environment, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"questionAttempts": 5' in result.stdout


@pytest.mark.parametrize("override,message", [
    ({"VERCEL_ENV": "production"}, "restricted to Preview"),
    ({"OPENROUTER_API_KEY": "synthetic-live-key"}, "Live provider keys are forbidden"),
    ({"GOOGLE_API_KEY": "synthetic-live-key"}, "Live provider keys are forbidden"),
    ({"XAI_API_KEY": "synthetic-live-key"}, "Live provider keys are forbidden"),
    ({"OLLAMA_FALLBACK_TO_OPENROUTER": "true"}, "without fallback"),
])
def test_artifact_refuses_production_live_keys_and_fallback(artifact, override, message):
    output, _ = artifact
    environment = dict(os.environ, PYTHONPATH=str(output), APP_ENV="test", VERCEL_ENV="preview",
                       OLLAMA_API_KEY="mock-only-not-a-real-provider-key", LLM_PROVIDER="ollama",
                       OPENROUTER_API_KEY="", GOOGLE_API_KEY="", XAI_API_KEY="",
                       OLLAMA_FALLBACK_TO_OPENROUTER="false")
    environment.update(override)
    result = subprocess.run([sys.executable, "-c", "from mock_preview import install; install()"],
                            cwd=output, env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert message in result.stderr
