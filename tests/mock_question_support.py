"""Keep the real question pipeline; replace only synthetic provider output."""

import json

from api import interview
from deployment.mock_questions import REQUEST, bind_request, question_bundle


def configure_questions(monkeypatch, *, count=5):
    service = interview.question_service
    monkeypatch.setattr(interview.settings, "MODEL_NAME", "test:free" if count == 1 else "gemma4:cloud")
    monkeypatch.setattr(service, "MODEL_NAME", interview.settings.MODEL_NAME)
    monkeypatch.setattr(service, "_get_client_or_none", lambda: object())
    requests, attempts = [], []
    generate = service.get_next_question_for_session

    def record(**kwargs):
        requests.append(kwargs)
        return generate(**kwargs)

    def reply(*args, **kwargs):
        attempts.append(REQUEST.get()["question_index"])
        return json.dumps(question_bundle(REQUEST.get()))

    monkeypatch.setattr(service, "get_next_question_for_session", bind_request(record))
    monkeypatch.setattr(service, "call_llm", reply)
    return requests, attempts
