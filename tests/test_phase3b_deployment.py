"""Cloud entrypoint and server-side Preview protection compatibility."""

from pathlib import Path
from time import monotonic

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from interview_app_backend.llm import deadline
from interview_app_frontend.services.api_client import InterviewAPIClient


def test_preview_bypass_is_header_only_and_redirects_are_blocked(monkeypatch):
    monkeypatch.setenv("VERCEL_AUTOMATION_BYPASS_SECRET", "preview-test-bypass")
    requests = []

    def redirect(request):
        requests.append(request)
        return httpx.Response(307, headers={"Location": "https://other.example/api/interview/context"})

    client = InterviewAPIClient(base_url="https://preview.example", secret="backend-test-secret",
                                transport=httpx.MockTransport(redirect))
    from interview_app_frontend.services.api_client import BackendError
    with pytest.raises(BackendError):
        client.context(role="Backend Engineer")
    assert len(requests) == 1
    assert requests[0].headers["x-vercel-protection-bypass"] == "preview-test-bypass"
    assert requests[0].headers["Authorization"] == "Bearer backend-test-secret"
    assert b"preview-test-bypass" not in requests[0].content
    assert b"backend-test-secret" not in requests[0].content


def test_preview_bypass_is_optional(monkeypatch):
    monkeypatch.delenv("VERCEL_AUTOMATION_BYPASS_SECRET", raising=False)
    client = InterviewAPIClient(secret="test")
    assert client.preview_bypass == ""


def test_cloud_entrypoint_renders_existing_welcome_screen():
    entrypoint = Path(__file__).resolve().parents[1] / "deployment/streamlit/app.py"
    ui = AppTest.from_file(str(entrypoint)).run()
    assert not ui.exception
    assert ui.button(key="welcome_start_setup")


def test_cloud_frontend_manifest_resolves_to_frontend_only_requirements():
    manifest = Path("deployment/streamlit/requirements.txt")
    include = manifest.read_text().strip().removeprefix("-r ")
    packages = (manifest.parent / include).resolve().read_text()
    assert "streamlit==" in packages
    for excluded in ("openai", "fastapi", "uvicorn", "google-generativeai", "playwright"):
        assert excluded not in packages


def test_truncated_backoff_fails_even_if_timer_wakes_early(monkeypatch):
    budget = deadline.Deadline(monotonic() + 1)
    token = deadline.current_deadline.set(budget)
    monkeypatch.setattr(budget.cancelled, "wait", lambda timeout: False)
    try:
        with pytest.raises(deadline.DeadlineExceeded):
            deadline.pause(60)
    finally:
        deadline.current_deadline.reset(token)
