"""API adapters retain the real services and parsers, mocking only provider output."""

import json
from unittest.mock import Mock

from fastapi.testclient import TestClient

from api.index import app
from config import settings
from interview_app_backend.llm import client as llm
from interview_app_backend.services import evaluation_pipeline, evaluation_rules, evaluation_service, question_service
from tests.question_contract_fixtures import valid_bundle
from tests.relevance_regression_fixtures import verdict

HEADERS = {"Authorization": "Bearer llm-test-secret"}
QUESTION = "How would you diagnose a slow service and decide which improvement to make first?"
ANSWER = "I would measure request latency, identify the bottleneck and verify the change with a representative test."


def configure(monkeypatch):
    monkeypatch.setenv("BACKEND_API_SECRET", "llm-test-secret")
    monkeypatch.setenv("BACKEND_RATE_LIMIT", "1000")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "open-router")
    monkeypatch.setattr(settings, "MODEL_NAME", "test:free")
    monkeypatch.setattr(llm, "MODEL_NAME", "test:free")
    monkeypatch.setattr(llm, "get_fallback_chain", lambda *args, **kwargs: ["test:free"])
    monkeypatch.setattr(question_service, "MODEL_NAME", "test:free")
    monkeypatch.setattr(evaluation_pipeline, "MODEL_NAME", "test:free")
    sdk = Mock()
    monkeypatch.setattr(question_service, "get_openrouter_client", lambda: sdk)
    monkeypatch.setattr(evaluation_service, "get_openrouter_client", lambda: sdk)
    monkeypatch.setattr(evaluation_rules, "get_openrouter_client", lambda: sdk)
    app.middleware_stack = None
    return sdk


def test_question_uses_existing_service_and_output_validation(monkeypatch):
    sdk = configure(monkeypatch)
    bundle = valid_bundle()
    bundle["questions"] = bundle["questions"][:1]
    bundle["meta"]["total_questions"] = 1
    bundle["meta"]["distribution"] = {key: int(key == "cv_based") for key in bundle["meta"]["distribution"]}
    sdk.responses.create.return_value = Mock(output_text=json.dumps(bundle))
    with TestClient(app) as client:
        response = client.post("/api/interview/question", headers=HEADERS,
                               json={"role": "Backend Engineer", "question_type": "cv_based"})
    assert response.status_code == 200
    assert response.json()["questions"][0]["question"] == bundle["questions"][0]["question"]
    assert sdk.responses.create.call_count == 1


def test_evaluation_runs_existing_pipeline_with_mocked_llm_json(monkeypatch):
    sdk = configure(monkeypatch)
    scores = dict.fromkeys(("technical_accuracy", "clarity", "relevance", "structure", "specificity",
                           "communication", "problem_solving_approach"), 7)
    coaching = {"summary": "The response proposes measurement and verification.",
                "strengths": ["You identify the bottleneck."], "key_issues": [], "improvements": []}
    support = [{"claim": coaching["strengths"][0], "question_quote": "diagnose a slow service",
                "answer_quote": "identify the bottleneck"}]
    outputs = [
        verdict(QUESTION, ANSWER),
        {"has_metrics": False, "has_reasoning": True, "has_structure": True},
        {"evidence": {"metrics": [], "actions": ["measure request latency"], "reasoning": "verify the change"},
         "scores": scores, "feedback": coaching, "feedback_support": support},
        {"feedback": coaching, "feedback_support": support},
    ]
    sdk.responses.create.side_effect = [Mock(output_text=json.dumps(output)) for output in outputs]
    with TestClient(app) as client:
        response = client.post("/api/interview/evaluate", headers=HEADERS, json={"question": QUESTION, "answer": ANSWER})
    assert response.status_code == 200
    result = response.json()
    assert result["scores"]["relevance"] == 7
    assert result["overall_decision"] == "pass"
    assert result["evaluation_pipeline"]["grounded"]
    assert result["trust"]
    assert result["follow_up"]["question"]
    assert sdk.responses.create.call_count in {3, 4}
