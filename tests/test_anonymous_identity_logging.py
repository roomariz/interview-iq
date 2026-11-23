"""Anonymous identity validation and normal-log privacy regressions."""

import logging
import time

import pytest

from shared.visitor_identity import TTL, issue, validate

KEY = "synthetic-visitor-signing-key-00000000"


def test_random_signed_identities():
    tokens = [issue(KEY) for _ in range(100)]
    assert len(set(tokens)) == 100
    assert len({validate(token, KEY) for token in tokens}) == 100
    token = tokens[0]
    for invalid in ("", "chosen-id", "a" * 10000, token[:-1], token + "x", token.replace("v1", "v2")):
        with pytest.raises(ValueError):
            validate(invalid, KEY)
    with pytest.raises(ValueError):
        validate(token, "different-key")


def test_token_expiry_future_and_tampering(monkeypatch):
    now = int(time.time())
    monkeypatch.setattr("shared.visitor_identity.time.time", lambda: now)
    token = issue(KEY)
    altered = token[:15] + "a" * 64 + token[79:]
    with pytest.raises(ValueError):
        validate(altered, KEY)
    for when in (now - 1, now + TTL, now + TTL + 1):
        monkeypatch.setattr("shared.visitor_identity.time.time", lambda: when)
        with pytest.raises(ValueError):
            validate(token, KEY)


def test_session_identity_stable_and_separate(monkeypatch):
    from interview_app_frontend.services.visitor import session_token
    import streamlit as st
    first, second = {}, {}
    monkeypatch.setattr(st, "session_state", first)
    a = session_token(KEY)
    assert a == session_token(KEY)
    monkeypatch.setattr(st, "session_state", second)
    assert session_token(KEY) != a
    monkeypatch.setattr(st, "session_state", first)
    assert session_token(KEY) == a


def test_logs_keep_status_duration_without_sensitive_data():
    import io
    from interview_app_backend.utils.private_logging import install, PrivateFields, DiagnosticFormatter
    install()
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.addFilter(PrivateFields())
    handler.setFormatter(DiagnosticFormatter("%(levelname)s %(message)s"))
    sensitive = "https://private.redis.example credential-value CV-sensitive Authorization: Bearer private-token"
    for name in ("httpx", "httpcore", "openai", "app", "llm", "interview.security"):
        logger = logging.getLogger(name)
        previous = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            logger.error("Failure %s", sensitive, extra={"body": sensitive, "headers": sensitive},
                         exc_info=(ValueError, ValueError(sensitive), None))
            logger.warning(sensitive)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous)
    logger = logging.getLogger("interview.security")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info("request_complete", extra={"status_code": 429, "duration_ms": 17})
    logger.removeHandler(handler)
    logs = output.getvalue()
    for value in sensitive.split():
        assert value not in logs
    assert "status_code=429 duration_ms=17" in logs
    assert "request_complete" in logs
