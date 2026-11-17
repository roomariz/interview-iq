import json
from unittest.mock import Mock

import pytest

from tests.relevance_regression_fixtures import verdict
from config import settings
from interview_app_backend.llm import client as llm
from interview_app_backend.llm import ollama_client
from interview_app_backend.services import evaluation_service, question_service

QUESTION = "Describe a time you improved system performance under constraints."
ANSWER = "I profiled the slow Python API, cached repeated database queries and measured latency before and after the change."
SCORE_PAYLOAD = {
    "evidence": {"metrics": [], "actions": ["profiled API"], "reasoning": "Reduced repeated database work"},
    "scores": {"technical_accuracy": 7, "clarity": 7, "relevance": 7, "structure": 7,
               "specificity": 7, "communication": 7, "problem_solving_approach": 7},
    "strengths": ["Concrete action"], "improvement_areas": ["Quantify the result"],
    "overall_summary": "Relevant example with limited measurements.",
}


@pytest.fixture
def transport(monkeypatch):
    for name, value in {
        "LLM_PROVIDER": "ollama", "OLLAMA_API_KEY": "test-key", "OLLAMA_MODEL": "gemma4:cloud",
        "OLLAMA_HOST": "https://ollama.com", "OLLAMA_FALLBACK_TO_OPENROUTER": False,
        "MODEL_NAME": "gemma4:cloud",
    }.items():
        monkeypatch.setattr(settings, name, value)
    monkeypatch.setattr(question_service, "MODEL_NAME", "gemma4:cloud")
    monkeypatch.setattr(ollama_client.time, "sleep", Mock())
    post = Mock()
    monkeypatch.setattr(ollama_client.requests, "post", post)
    yield post
    llm.clear_last_llm_call_metadata()


def envelope(content):
    text = content if isinstance(content, str) else json.dumps(content)
    return Mock(status_code=200, json=Mock(return_value={"message": {"content": text}, "done": True}))


def question_bundle():
    types = ["cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"]
    scenarios = ["debugging", "performance", "behavioural", "system_design", "scaling"]
    questions = [
        "A recent change caused a production issue in your API backend, implemented in Python. How would you debug and resolve the regression?",
        "A Python database query slows your API. How would you measure and improve the performance?",
        "Your team disagrees about a Python API release. How would you communicate the risks to stakeholders?",
        "Your Python API needs to scale. How would you design the system and compare the trade-offs?",
        "Your Python API receives ten times more requests. How would you coordinate a safe scaling plan?",
    ]
    return {
        "meta": {"total_questions": 5, "distribution": dict.fromkeys(types, 1)},
        "questions": [
            {"sequence_order": index + 1, "question": question, "question_type": types[index],
             "scenario_type": scenarios[index], "focus_area": "performance", "difficulty_level": "Medium",
             "what_interviewer_is_testing": ["Investigation"],
             "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": [], "gap_used": None}}
            for index, question in enumerate(questions)
        ],
    }


def test_existing_question_service_uses_ollama_despite_legacy_provider_argument(transport):
    payload = question_bundle()
    payload["questions"] = payload["questions"][:1]
    payload["questions"][0]["focus_area"] = "debugging"
    payload["meta"] = {"total_questions": 1, "distribution": {
        "cv_based": 1, "jd_based": 0, "behavioural": 0, "deep_dive": 0, "gap_targeted": 0,
    }}
    transport.return_value = envelope(payload)
    result = question_service.get_next_question("Backend Engineer", "Medium", "Friendly", "Concise", "Python API experience")
    assert result == payload["questions"][0]["question"]
    assert llm.get_last_llm_call_metadata()["provider"] == "ollama"
    assert "Return only valid JSON" in transport.call_args.kwargs["json"]["messages"][0]["content"]


def test_question_schema_failure_retries_before_success(transport):
    transport.side_effect = [envelope({"question": "Wrong strict schema?"}), envelope(question_bundle())]
    output = llm.call_llm("schema prompt", llm.get_openrouter_client(), task="question_generation.cv_based")
    assert json.loads(output)["meta"]["total_questions"] == 5
    assert transport.call_count == 2


def test_existing_evaluator_validates_evidence_and_scores(transport):
    repair = {"feedback": {"strengths": ["Concrete action"], "key_issues": [], "improvements": []},
              "feedback_support": [{"claim": "Concrete action", "question_quote": QUESTION, "answer_quote": ANSWER}]}
    transport.side_effect = [envelope("YES"), envelope({"has_reasoning": True}),
                             envelope(SCORE_PAYLOAD), envelope(repair)]
    result = evaluation_service.evaluate_answer(QUESTION, ANSWER)
    assert "scores" in result
    assert result["answer"] == ANSWER
    assert result["evaluation_context"]["has_reasoning"] is True
    assert transport.call_count == 4
    prompts = [call.kwargs["json"]["messages"][-1]["content"] for call in transport.call_args_list]
    assert "scores" in prompts[2]
    assert prompts[3].startswith("Repair coaching feedback only")
    assert result["feedback"]["strengths"] == ["Concrete action"]
    assert all(type(value) is int and 0 <= value <= 10 for value in result["scores"].values())


def test_failed_ollama_scoring_returns_no_placeholder_result(transport, monkeypatch):
    monkeypatch.setattr(evaluation_service, "is_answer_relevant", lambda *args: True)
    transport.return_value = envelope("invalid JSON")
    with pytest.raises(RuntimeError, match="no scores were recorded"):
        evaluation_service.evaluate_submission(QUESTION, ANSWER)


def test_off_topic_answer_preserves_existing_relevance_gate(transport):
    answer = "I love baking cakes and watching football with my friends."
    transport.return_value = envelope(verdict(QUESTION, answer, "off_topic", "behavioural"))
    result = evaluation_service.evaluate_submission(QUESTION, answer)
    assert result["relevance_gate_applied"] is True
    assert result["overall_decision"] == "fail"
    assert result["trust"]["score_confidence"] == 0.0
    assert transport.call_count == 1


def test_plain_text_example_answer_remains_supported(transport):
    transport.return_value = envelope("I profiled the API and reduced repeated queries.")
    assert evaluation_service.generate_example_answer(ANSWER) == "I profiled the API and reduced repeated queries."
    assert len(transport.call_args.kwargs["json"]["messages"]) == 1


def test_openrouter_sdk_supports_existing_responses_calls_without_network():
    with llm.create_openrouter_client("test-key") as client:
        assert callable(client.responses.create)
        assert str(client.base_url) == "https://openrouter.ai/api/v1/"


def test_openrouter_evidence_uses_evidence_schema():
    client = Mock()
    client.responses.create.return_value = Mock(output_text='{"has_reasoning": true}')
    assert llm.call_llm("evidence prompt", client, task="evaluation.evidence_extraction") == '{"has_reasoning": true}'
