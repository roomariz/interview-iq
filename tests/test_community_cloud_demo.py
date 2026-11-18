"""The cloud demonstration fails closed and labels every displayed assessment."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from interview_app_frontend.services.community_cloud import MOCK_BACKEND_URL, validate_configuration


@pytest.fixture
def cloud(monkeypatch):
    values = {"BACKEND_API_URL": MOCK_BACKEND_URL, "BACKEND_API_SECRET": "a" * 48,
              "BACKEND_VISITOR_SIGNING_KEY": "b" * 48,
              "VERCEL_AUTOMATION_BYPASS_SECRET": "synthetic-platform-secret"}
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


def test_approved_configuration(cloud):
    validate_configuration()


@pytest.mark.parametrize("name,value", [
    ("BACKEND_API_URL", "https://interviewiq-api-preview-5s3zjgygk-roomas-projects.vercel.app"),
    ("BACKEND_API_URL", "https://interviewiq-api-preview-14932zvli-roomas-projects.vercel.app"),
    ("BACKEND_API_URL", MOCK_BACKEND_URL + "?bypass=private"),
    ("BACKEND_API_URL", "http://127.0.0.1:8000"),
    ("BACKEND_API_SECRET", ""), ("BACKEND_API_SECRET", "REPLACE_WITH_SECRET"),
    ("BACKEND_VISITOR_SIGNING_KEY", "short"),
    ("BACKEND_VISITOR_SIGNING_KEY", "a" * 48),
    ("VERCEL_AUTOMATION_BYPASS_SECRET", ""),
])
def test_bad_cloud_configuration_is_rejected(cloud, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError) as error:
        validate_configuration()
    assert not any(secret in str(error.value) for secret in list(cloud.values())[1:])


def test_bad_configuration_stops_before_welcome(cloud, monkeypatch):
    monkeypatch.setenv("BACKEND_API_URL", "https://wrong.example")
    path = Path(__file__).resolve().parents[1] / "deployment/streamlit/app.py"
    ui = AppTest.from_file(str(path)).run()
    assert not ui.exception
    assert ui.error
    assert not ui.button


def test_missing_cloud_secrets_stops_without_backend_requests(monkeypatch):
    for key in ("BACKEND_API_URL", "BACKEND_API_SECRET", "BACKEND_VISITOR_SIGNING_KEY",
                "VERCEL_AUTOMATION_BYPASS_SECRET"):
        monkeypatch.setenv(key, "")
    def forbidden(*args, **kwargs):
        pytest.fail("The inactive deployment must not contact the backend")
    monkeypatch.setattr("httpx.Client.send", forbidden)
    path = Path(__file__).resolve().parents[1] / "deployment/streamlit/app.py"
    ui = AppTest.from_file(str(path)).run()
    assert not ui.exception and ui.error and not ui.button


def test_private_streamlit_secrets_are_used_only_in_server_headers(monkeypatch):
    import httpx
    from shared.visitor_identity import validate

    values = {"BACKEND_API_URL": MOCK_BACKEND_URL, "BACKEND_API_SECRET": "a" * 48,
              "BACKEND_VISITOR_SIGNING_KEY": "b" * 48,
              "VERCEL_AUTOMATION_BYPASS_SECRET": "private-synthetic-bypass"}
    for key in values:
        monkeypatch.delenv(key, raising=False)
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(401, json={"error": {"code": "unauthorised"}})
    monkeypatch.setattr("httpx.HTTPTransport.handle_request",
                        lambda transport, request: httpx.MockTransport(respond).handle_request(request))
    ui = AppTest.from_string(
        "import streamlit as st\n"
        "from interview_app_frontend.services.community_cloud import validate_configuration\n"
        "from interview_app_frontend.services.api_client import InterviewAPIClient, BackendError\n"
        "validate_configuration()\n"
        "try:\n    InterviewAPIClient().context(role='Backend Engineer')\n"
        "except BackendError:\n    st.info('Synthetic connection checked')\n"
    )
    ui.secrets.update(values)
    ui.run()
    assert not ui.exception and len(requests) == 1
    request = requests[0]
    assert request.headers["Authorization"] == "Bearer " + values["BACKEND_API_SECRET"]
    assert request.headers["x-vercel-protection-bypass"] == values["VERCEL_AUTOMATION_BYPASS_SECRET"]
    validate(request.headers["X-Interview-Visitor"], values["BACKEND_VISITOR_SIGNING_KEY"])
    rendered = "\n".join(str(element.proto) for group in (
        ui.info, ui.error, ui.warning, ui.markdown, ui.code) for element in group)
    assert all(value not in rendered and value not in str(request.url)
               and value not in request.content.decode() for value in list(values.values())[1:])


def test_downloaded_feedback_identifies_demonstration_without_credentials(cloud, monkeypatch):
    import json
    import streamlit as st

    payloads = []
    original = st.download_button
    def capture(*args, **kwargs):
        payloads.append(json.loads(kwargs["data"]))
        return original(*args, **kwargs)
    monkeypatch.setattr(st, "download_button", capture)
    ui = AppTest.from_string(
        "import streamlit as st\n"
        "from interview_app_frontend.app import main\n"
        "st.session_state.current_screen='feedback'\n"
        "main(demonstration=True)\n"
    ).run()
    assert not ui.exception and len(payloads) == 1
    assert payloads[0]["demonstration"]["mocked"] is True
    assert "not a verified live AI assessment" in payloads[0]["demonstration"]["notice"]
    assert not any(name in json.dumps(payloads) for name in (
        "BACKEND_API_SECRET", "BACKEND_VISITOR_SIGNING_KEY", "VERCEL_AUTOMATION_BYPASS_SECRET"))
    assert all(value not in json.dumps(payloads) for value in list(cloud.values())[1:])


@pytest.mark.parametrize("screen", ["welcome", "setup", "question", "generating_question",
                                   "evaluating_answer", "sample_answer", "summary", "feedback"])
def test_demonstration_notice_covers_all_feedback_screens(screen):
    ui = AppTest.from_string(
        "from interview_app_frontend.app import main\nmain(demonstration=True)\n"
    ).run()
    ui.session_state["current_screen"] = screen
    ui.session_state["session_complete"] = screen == "summary"
    from concurrent.futures import Future
    if screen == "generating_question":
        ui.session_state["question_generation_future"] = Future()
    if screen == "evaluating_answer":
        ui.session_state["answer_evaluation_future"] = Future()
    ui.run()
    assert not ui.exception
    assert "Demonstration only" in ui.warning[0].value
    assert "confidence, follow-ups, sample answers and session summaries" in ui.warning[0].value
