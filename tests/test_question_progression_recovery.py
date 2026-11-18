"""Frontend job failures preserve the current step until an explicit retry."""

from concurrent.futures import Future
from unittest.mock import Mock

import pytest

from interview_app_frontend.services.api_client import BackendError
from interview_app_frontend.state import question_generation_job as jobs


@pytest.mark.parametrize("result", [{"questions": []}, {"questions": [{}]}, None])
def test_empty_or_invalid_batch_preserves_session(result):
    future = Future()
    future.set_result(result)
    answers = [{"question": "A previously evaluated question?", "scores": {"relevance": 7}}]
    state = {"question_generation_future": future, "current_question_index": 2,
             "answers": answers, "_anonymous_visitor_token": "same-identity", "has_active_session": True}
    assert jobs.poll_question_generation(state)
    assert state["current_screen"] == "generating_question"
    assert state["question_job"]["status"] == "failed"
    assert state["answers"] is answers
    assert state["current_question_index"] == 2
    assert state["_anonymous_visitor_token"] == "same-identity"
    assert state["has_active_session"]
    assert not jobs.poll_question_generation(state)


def test_pending_or_unconsumed_request_is_not_dispatched_twice(monkeypatch):
    client = Mock()
    monkeypatch.setattr(jobs, "InterviewAPIClient", client)
    future = Future()
    state = {"question_generation_future": future}
    jobs.begin_question_generation(state)
    future.set_result({"questions": [{"question": "A newly generated question?"}], "meta": {}})
    jobs.begin_question_generation(state)
    client.assert_not_called()
    assert jobs.poll_question_generation(state)
    assert state["current_question"] == "A newly generated question?"


def test_api_error_is_safe_and_does_not_consume_another_question():
    future = Future()
    future.set_exception(BackendError("Please wait before trying again."))
    state = {"question_generation_future": future, "current_question_index": 3, "answers": [{}, {}]}
    assert jobs.poll_question_generation(state)
    assert state["question_generation_error"] == "Please wait before trying again."
    assert state["current_question_index"] == 3
    assert len(state["answers"]) == 2
    assert not jobs.poll_question_generation(state)
