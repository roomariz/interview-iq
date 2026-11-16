import json
from unittest.mock import Mock

import pytest

from interview_app_backend.llm import client as llm
from interview_app_backend.services import evaluation_service as service
from interview_app_backend.services.relevance_assessment import parse_relevance, relevance_prompt
from interview_app_backend.services.evaluation_rules import is_answer_relevant
from interview_app_frontend.utils.pipeline_view import build_reliability_card
from tests.relevance_regression_fixtures import ANSWER, INCORRECT_EVALUATION, QUESTION, verdict


@pytest.fixture
def evaluation(monkeypatch):
    monkeypatch.setattr(service, "_get_evaluation_client", lambda: object())
    monkeypatch.setattr(service, "generate_reference_answer", lambda question: "Unrelated model reference")
    monkeypatch.setattr(service, "calculate_semantic_similarity", lambda *args: 0.01)
    monkeypatch.setattr(service, "extract_evidence_context", lambda *args, **kwargs: {
        "has_metrics": False, "has_structure": True, "has_reasoning": True,
        "has_tradeoffs": True, "has_alternatives": True, "impact_strength": "weak",
        "confidence": {"structure": 0.9, "reasoning": 0.9},
        "anomaly_flags": [], "contradiction_flags": [],
    })
    # Test scores represent a provider response, never a production fallback.
    scoring = Mock(return_value=json.dumps({
        "scores": dict.fromkeys(("technical_accuracy", "clarity", "relevance", "structure",
                                 "specificity", "communication", "problem_solving_approach"), 7),
        "labels": {}, "feedback": {"summary": "Applicable approach"},
        "follow_up": INCORRECT_EVALUATION["follow_up"],
    }))
    monkeypatch.setattr(service, "call_llm", scoring)
    monkeypatch.setattr("interview_app_backend.services.evaluation_rules._get_single_provider_client", lambda: object())
    return scoring


def test_verbatim_release_regression_survives_pipeline_without_metrics_or_star(evaluation, monkeypatch):
    relevance = Mock(return_value=json.dumps(verdict()))
    monkeypatch.setattr(llm, "call_llm", relevance)
    result = service.evaluate_submission(QUESTION, ANSWER)
    assert result["question"] == QUESTION
    assert result["answer"] == ANSWER
    assert result["topic_match"] is True
    assert result["relevance_gate_applied"] is False
    assert result["failure_type"] != "off_topic"
    assert result["scores"]["specificity"] == 7  # No no-metrics cap for a scenario.
    assert relevance.call_count == 1
    assert evaluation.call_count == 2  # One bounded feedback-only repair.
    prompt = evaluation.call_args_list[0].args[0]
    assert QUESTION in prompt and ANSWER in prompt
    followup = result["follow_up"]["question"]
    assert QUESTION not in followup and "rollback" in followup
    assert "real example" not in followup
    assert "STAR are not required" in prompt
    card = build_reliability_card(result, {})
    assert card["confidence"] == result["evaluation_summary"]["confidence_label"]
    assert result["trust"]["decision_confidence"] == result["overall_decision_detail"]["decision_confidence"]
    assert "trust" not in result["validation_warning"]


@pytest.mark.parametrize("question,answer,kind,status", [
    (QUESTION, ANSWER, "scenario_troubleshooting", "relevant"),
    ("How does a hash table resolve collisions?", "Chaining stores colliding entries in a bucket; probing searches another slot.", "technical_knowledge", "relevant"),
    ("Design a reliable notification service.", "I would queue messages, retry deliveries and deduplicate by message identifier.", "system_design", "relevant"),
    ("How would you optimise a slow query?", "I would examine the execution plan and benchmark an index against representative data.", "performance_optimisation", "relevant"),
    ("Tell me about a disagreement with a colleague.", "We disagreed over priorities. I listened and proposed a compromise we both accepted.", "behavioural", "relevant"),
    (QUESTION, "I would check the logs, though I am unsure how to recover safely.", "scenario_troubleshooting", "partial"),
])
def test_question_types_and_partial_answers_remain_relevant(evaluation, monkeypatch, question, answer, kind, status):
    monkeypatch.setattr(llm, "call_llm", lambda *args, **kwargs: json.dumps(verdict(question, answer, status, kind)))
    result = service.evaluate_submission(question, answer)
    assert result["failure_type"] != "off_topic"
    assert result["relevance_assessment"]["question_type"] == kind


def test_genuine_off_topic_requires_semantic_evidence(evaluation, monkeypatch):
    answer = "I spend weekends baking cakes and playing football with friends."
    monkeypatch.setattr(llm, "call_llm", lambda *args, **kwargs: json.dumps(verdict(QUESTION, answer, "off_topic")))
    result = service.evaluate_submission(QUESTION, answer)
    evaluation.assert_not_called()
    assert result["failure_type"] == "off_topic"
    assert result["overall_decision"] == "fail"
    assert result["trust"]["decision_confidence"] == "high"
    assert result["trust"]["score_confidence"] == 0.0
    assert result["validation_warning"]["validation"]["score_confidence"] == 0.0
    assert QUESTION in result["follow_up"]["question"]
    assert "system performance" not in result["follow_up"]["question"]


@pytest.mark.parametrize("payload", ["NO", "YES and NO", "invalid", "{}",
    json.dumps(verdict(status="off_topic", confidence=0.6)),
    json.dumps({**verdict(status="off_topic"), "question_quote": "a different question"}),
    json.dumps({**verdict(status="off_topic"), "answer_quote": "invented evidence"}),
])
def test_uncertain_verdicts_never_force_off_topic(evaluation, monkeypatch, payload):
    monkeypatch.setattr(llm, "call_llm", lambda *args, **kwargs: payload)
    result = service.evaluate_submission(QUESTION, ANSWER)
    assert result["failure_type"] != "off_topic"
    assert result["trust"]["trust_level"] == "low"
    assert result["trust"]["decision_confidence"] == "low"
    assert result["validation_warning"]["validation"]["trust_level"] == "low"
    assert result["overall_decision_detail"]["trust_level"] == "low"
    assert result["evaluation_summary"]["confidence_label"] == "Low"


def test_provider_failure_is_uncertain_without_keyword_gate(evaluation, monkeypatch):
    monkeypatch.setattr(llm, "call_llm", Mock(side_effect=RuntimeError("unavailable")))
    assert is_answer_relevant("Explain mutual exclusion.", "Only one thread enters the protected section at once.")


def test_successive_questions_do_not_reuse_relevance_or_reference_context(evaluation, monkeypatch):
    questions = [(QUESTION, ANSWER), ("Explain mutual exclusion.",
                  "Only one thread enters the protected section at once.")]
    relevance = Mock(side_effect=[json.dumps(verdict(q, a)) for q, a in questions])
    monkeypatch.setattr(llm, "call_llm", relevance)
    for question, answer in questions:
        result = service.evaluate_submission(question, answer)
        assert result["question"] == question and result["answer"] == answer
    prompts = [call.args[0] for call in relevance.call_args_list]
    assert QUESTION in prompts[0] and QUESTION not in prompts[1]
    assert "Unrelated model reference" not in " ".join(prompts)


def test_reported_incorrect_scoring_is_rejected_without_inventing_scores(evaluation, monkeypatch):
    monkeypatch.setattr(llm, "call_llm", lambda *args, **kwargs: json.dumps(verdict()))
    evaluation.return_value = json.dumps(INCORRECT_EVALUATION)
    with pytest.raises(RuntimeError, match="no scores were recorded"):
        service.evaluate_submission(QUESTION, ANSWER)


def test_relevance_prompt_has_only_current_inputs_and_no_fixed_target():
    prompt = relevance_prompt(QUESTION, ANSWER)
    assert json.loads(prompt.split("Input:\n")[1]) == {"question": QUESTION, "answer": ANSWER}
    assert "Does this answer directly address the question about system performance" not in prompt
    assert "Missing metrics, STAR" in prompt
    assert parse_relevance(json.dumps(verdict()), QUESTION, ANSWER)["status"] == "relevant"


@pytest.mark.parametrize("provider", ["google", "ollama", "open-router"])
def test_provider_transports_preserve_question_bound_verdict(evaluation, monkeypatch, provider):
    from config import settings
    from interview_app_backend.llm.ollama_client import OllamaCloudClient

    monkeypatch.setattr(settings, "LLM_PROVIDER", provider)
    transport = Mock()
    content = json.dumps(verdict())
    transport.responses.create.return_value = {"output_text": content}
    transport.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content=content), finish_reason="stop")])
    if provider == "ollama":
        monkeypatch.setattr(OllamaCloudClient, "call", Mock(return_value=content))
        transport = OllamaCloudClient()
    monkeypatch.setattr("interview_app_backend.services.evaluation_rules._get_single_provider_client", lambda: transport)
    result = service.evaluate_submission(QUESTION, ANSWER)
    assert result["topic_match"] is True
    assert result["relevance_gate_applied"] is False
    assert result["relevance_assessment"]["provider_call"]["task"] == "evaluation.relevance_check"
    llm.clear_last_llm_call_metadata()


@pytest.mark.parametrize("status,expected_gate", [("relevant", False), ("off_topic", True)])
def test_opt_in_provider_fallback_preserves_relevance_contract(evaluation, monkeypatch, status, expected_gate):
    from config import settings
    from interview_app_backend.llm.ollama_client import OllamaCloudClient

    answer = ANSWER if status == "relevant" else "I enjoy baking cakes and playing football with my friends."
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_FALLBACK_TO_OPENROUTER", True)
    monkeypatch.setattr(llm, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OllamaCloudClient, "call", Mock(side_effect=RuntimeError("provider unavailable")))
    fallback = Mock()
    fallback.responses.create.return_value = {"output_text": json.dumps(verdict(QUESTION, answer, status))}
    monkeypatch.setattr(llm, "create_openrouter_client", lambda key: fallback)
    monkeypatch.setattr("interview_app_backend.services.evaluation_rules._get_single_provider_client", OllamaCloudClient)
    result = service.evaluate_submission(QUESTION, answer)
    assert result["relevance_gate_applied"] is expected_gate
    assert result["relevance_assessment"]["provider_call"]["status"] == "success"
    assert QUESTION in fallback.responses.create.call_args.kwargs["input"]
    llm.clear_last_llm_call_metadata()
