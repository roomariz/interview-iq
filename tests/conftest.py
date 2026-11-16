"""Automated tests cannot contact paid providers or other external services."""

import socket

import pytest


@pytest.fixture(autouse=True, scope="session")
def block_external_network():
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded(original):
        def connect(sock, address):
            # Windows asyncio uses a loopback socket pair internally.
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original(sock, address)
            raise RuntimeError("External network access is disabled during automated tests")
        return connect

    # Keep the guard until process exit, including background worker shutdown.
    socket.socket.connect = guarded(original_connect)
    socket.socket.connect_ex = guarded(original_connect_ex)


@pytest.fixture(autouse=True)
def mock_setup_http_boundary_for_existing_unit_tests(request, monkeypatch):
    """Setup unit tests now mock the HTTP boundary; their assertions are unchanged."""
    from tests.phase2_legacy_support import LEGACY_UI_TESTS, configure_http_double
    if request.node.name in LEGACY_UI_TESTS:
        configure_http_double(request, monkeypatch)
        return
    if request.module.__name__ not in {"test_session_manager", "tests.test_session_manager"}:
        return
    if not request.node.name.startswith("test_start_interview"):
        return
    from unittest.mock import Mock
    from api.interview import context
    from shared.api_contracts import ContextRequest
    from interview_app_frontend.state import session_manager

    client = Mock()
    client.context.side_effect = lambda **kwargs: context(ContextRequest(**kwargs)).model_dump()
    monkeypatch.setattr(session_manager, "InterviewAPIClient", lambda: client)
    monkeypatch.setattr(session_manager, "begin_question_generation", lambda state: None)
