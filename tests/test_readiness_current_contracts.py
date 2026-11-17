"""Current-contract evidence for the retained legacy failure assessment."""

import copy
import json
from unittest.mock import Mock

import httpx
from openai import RateLimitError
import streamlit as st

from interview_app_backend.llm import client as llm
from interview_app_backend.services import evaluation_service as evaluation
from interview_app_backend.services.feedback_integrity import clean_feedback
from interview_app_backend.services.feedback_support import validate_feedback_support
from interview_app_frontend.state.session_feedback import _apply_answer_feedback
from interview_app_frontend.state.session_manager import ensure_session_state
from tests.test_ollama_workflows import ANSWER, QUESTION, SCORE_PAYLOAD


def test_provider_logging_retains_metadata_without_prompt_or_stdout(monkeypatch, caplog, capsys):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "open-router")
    monkeypatch.setattr(llm, "MODEL_NAME", "test-model")
    sdk = Mock()
    sdk.responses.create.return_value = {"output_text": "answer"}
    with caplog.at_level("INFO", logger="llm"):
        assert llm.call_llm("private synthetic interview input", sdk, task="general") == "answer"
    assert any(r.name == "llm" and r.getMessage() == "LLM_SUCCESS" and r.model == "test-model"
               and r.task == "general" for r in caplog.records)
    assert "private synthetic interview input" not in caplog.text
    assert capsys.readouterr().out == ""


def test_real_sdk_rate_limit_exception_retries_then_uses_existing_fallback(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "open-router")
    monkeypatch.setattr(llm, "MODEL_NAME", "first:free")
    monkeypatch.setattr(llm, "get_fallback_chain", lambda *a, **kw: ["first:free", "second:free"])
    monkeypatch.setattr(llm, "pause", lambda seconds: None)
    response = httpx.Response(429, request=httpx.Request("POST", "https://provider.example/responses"))
    error = RateLimitError("rate limited", response=response, body={"error": "rate limited"})
    sdk = Mock()
    sdk.responses.create.side_effect = [error, error, error, {"output_text": "answer"}]
    assert llm.call_llm("synthetic input", sdk) == "answer"
    assert [c.kwargs["model"] for c in sdk.responses.create.call_args_list] == ["first:free"] * 3 + ["second:free"]
    assert all(c.kwargs["timeout"] > 0 for c in sdk.responses.create.call_args_list)


def test_scoring_prompt_is_separate_and_feedback_repair_does_not_rescore(monkeypatch):
    repaired = {"feedback": {"strengths": ["Concrete action"], "key_issues": [], "improvements": []},
                "feedback_support": [{"claim": "Concrete action", "question_quote": QUESTION,
                                      "answer_quote": ANSWER}]}
    caller = Mock(side_effect=[json.dumps({"has_reasoning": True}), json.dumps(SCORE_PAYLOAD), json.dumps(repaired)])
    monkeypatch.setattr(evaluation, "get_openrouter_client", lambda: object())
    monkeypatch.setattr(evaluation, "call_llm", caller)
    result = evaluation.evaluate_answer(QUESTION, ANSWER, relevance_assessment={
        "status": "relevant", "question_type": "behavioural", "confidence": .9,
    })
    calls = caller.call_args_list
    assert [c.kwargs["task"] for c in calls] == [
        "evaluation.evidence_extraction", "evaluation.scoring", "evaluation.feedback_repair",
    ]
    assert calls[1].args[0].startswith(evaluation.EVALUATION_PROMPT)
    assert "Rewrite the answer to improve clarity" not in calls[1].args[0]
    assert calls[2].args[0].startswith("Repair coaching feedback only")
    caller.side_effect = [json.dumps({"has_reasoning": True}), json.dumps(SCORE_PAYLOAD), "{}"]
    without_repair = evaluation.evaluate_answer(QUESTION, ANSWER, relevance_assessment={
        "status": "relevant", "question_type": "behavioural", "confidence": .9,
    })
    assert result["scores"] == without_repair["scores"]
    assert result["feedback"]["strengths"] == ["Concrete action"]


def test_caching_strength_is_kept_with_current_input_quotes_and_withheld_without_them():
    question = "How did you improve service performance?"
    answer = "I implemented Redis caching for repeated database requests."
    claim = "Good use of caching"
    data = {"question": question, "answer": answer, "scores": {"relevance": 8},
            "feedback": {"strengths": [claim], "key_issues": [], "improvements": []}}
    cleaned = clean_feedback(data)
    raw = {"feedback_support": [{"claim": claim, "question_quote": question, "answer_quote": answer}]}
    supported = validate_feedback_support(copy.deepcopy(cleaned), raw, question, answer)
    withheld = validate_feedback_support(copy.deepcopy(cleaned), {}, question, answer)
    assert supported["feedback"]["strengths"] == [claim]
    assert withheld["feedback"]["strengths"] == []
    assert any(i["code"] == "missing_claim_support" for i in withheld["feedback_validation"]["issues"])


def test_real_session_defaults_and_trust_gate_control_memory():
    feedback = {"question": QUESTION, "answer": ANSWER, "scores": SCORE_PAYLOAD["scores"],
                "feedback": {"summary": "Concrete action", "strengths": ["Concrete action"],
                             "key_issues": [], "improvements": []},
                "memory_storage_allowed": True, "topic_match": True,
                "trust": {"trust_level": "high", "score_confidence": .9},
                "feedback_validation": {"status": "checked"}}
    st.session_state.clear()
    try:
        ensure_session_state()
        _apply_answer_feedback(st.session_state, QUESTION, ANSWER, feedback)
        assert len(st.session_state.future_session_memory) == 1
        assert st.session_state.answers[0]["answer"] == ANSWER
        st.session_state.future_session_memory = []
        feedback["trust"] = {}
        _apply_answer_feedback(st.session_state, QUESTION, ANSWER, feedback)
        assert st.session_state.future_session_memory == []
    finally:
        st.session_state.clear()
