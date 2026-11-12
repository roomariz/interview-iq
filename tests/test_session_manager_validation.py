import sys

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import pytest
import streamlit as st

from interview_app_frontend.state.session_manager import _is_valid_evaluation_for_storage


class TestIsValidEvaluationForStorage:
    def test_valid_evaluation_with_all_dimensions(self):
        feedback = {
            "scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}
        }
        assert _is_valid_evaluation_for_storage(feedback) is True

    def test_empty_scores_dict(self):
        feedback = {"scores": {}}
        assert _is_valid_evaluation_for_storage(feedback) is False

    def test_partial_scores(self):
        feedback = {"scores": {"relevance": 7}}
        assert _is_valid_evaluation_for_storage(feedback) is False

    def test_none_scores(self):
        feedback = {"scores": None}
        assert _is_valid_evaluation_for_storage(feedback) is False

    def test_missing_scores_key(self):
        feedback = {"question": "Q1", "answer": "A1"}
        assert _is_valid_evaluation_for_storage(feedback) is False