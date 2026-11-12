import unittest
from time import sleep, time
from unittest.mock import patch
import sys
from concurrent.futures import Future

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import streamlit as st
from unittest.mock import MagicMock

import interview_app_frontend.app as app_module
from interview_app_frontend.app import main
from interview_app_frontend.components.shell import SETUP_WIDGET_KEYS
from interview_app_backend.services.question_generation_job import poll_question_generation
from interview_app_frontend.components.answer_evaluation_screen import render_answer_evaluation
from interview_app_frontend.components.question_screen import render_question_and_answer
from interview_app_frontend.state.session_manager import start_interview
from interview_app_backend.services.question_service import get_next_question_for_session


class TestFullQuestionLoop(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()

    def _wait_for_generation(self, timeout: float = 1.0) -> None:
        deadline = time() + timeout
        while time() < deadline:
            if poll_question_generation(st.session_state):
                return
            sleep(0.01)

    def test_session_question_flow_progresses_across_multiple_turns(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            client = object()
            mock_client_factory.return_value = client
            mock_call_llm.side_effect = [
                "How would you apply your experience?",
                "How would you apply your experience?",
                "How would you apply your experience?",
            ]

            first = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=1,
                jd_context="",
                asked_topics=[],
                focus="",
                previous_questions=[],
            )
            second = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=2,
                jd_context="",
                asked_topics=[],
                focus="",
                previous_questions=[first],
            )
            third = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=3,
                jd_context="",
                asked_topics=[],
                focus="",
                previous_questions=[first, second],
            )

        self.assertIn("python", first.lower())
        self.assertIn("api", first.lower())
        self.assertNotEqual(first, second)
        self.assertIn("python", second.lower())
        self.assertIn("api", second.lower())
        self.assertNotEqual(second, third)
        self.assertIn("python", third.lower())
        self.assertIn("api", third.lower())
        self.assertGreaterEqual(mock_call_llm.call_count, 3)

    def test_repeated_topic_is_avoided_in_prompt(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.return_value = "How do you improve API reliability?"

            get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=2,
                jd_context="APIs",
                asked_topics=["APIs", "Reliability"],
                focus="",
                previous_questions=["How do you improve API reliability?"],
            )

        prompt = mock_call_llm.call_args.args[0]
        self.assertIn("CV: Python", prompt)
        self.assertIn("JOB_DESCRIPTION: APIs", prompt)
        self.assertIn("GAP_ANALYSIS (for ONE question only):", prompt)

    def test_question_topics_are_persisted_after_start(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Built APIs and improved performance."
        st.session_state.setup_job_description = "Backend role focused on APIs and performance."

        with patch(
            "interview_app_backend.services.question_generation_job.get_next_question_for_session",
            return_value="A user reports that a page in your application is slow due to API latency. How would you investigate and improve performance?",
        ):
            start_interview()
        self._wait_for_generation()

        self.assertTrue(st.session_state.question_topics)

    def test_duplicate_topic_failure_falls_back(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [
                "How do you optimise API performance in Python?",
                "How do you optimise API performance in Python?",
                "How do you optimise API performance in Python?",
            ]

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python APIs",
                question_index=1,
                jd_context="API performance",
                asked_topics=[],
                focus="",
            )

        self.assertIn("python", result.lower())
        self.assertIn("api", result.lower())
        self.assertTrue(result.endswith("?"))

    def test_navigation_keeps_session_state_intact(self):
        st.session_state.clear()
        st.session_state.current_screen = "setup"
        st.session_state.has_active_session = True
        st.session_state.session_complete = False
        st.session_state.current_question_index = 2

        with patch("interview_app_frontend.app.st.set_page_config"), patch(
            "interview_app_frontend.app.ensure_session_state"
        ) as mock_ensure, patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ) as mock_render:
            main()

        self.assertEqual(st.session_state.current_screen, "setup")
        self.assertTrue(st.session_state.has_active_session)
        self.assertEqual(st.session_state.current_question_index, 2)
        mock_ensure.assert_called_once()
        mock_render.assert_called_once()

    def test_main_logs_resolved_model_name_on_startup(self):
        st.session_state.clear()
        with patch("interview_app_frontend.app.st.set_page_config"), patch(
            "interview_app_frontend.app.ensure_session_state"
        ), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ), patch("interview_app_frontend.app.LOGGER.info") as mock_log:
            main()

        mock_log.assert_any_call("Resolved OpenRouter model: %s", app_module.MODEL_NAME)

    def test_main_does_not_render_request_log_on_question_screen(self):
        st.session_state.clear()
        st.session_state.current_screen = "question"
        st.session_state.request_log = [
            {
                "timestamp": 0,
                "task": "answer_evaluation",
                "provider": "open-router",
                "model": "google/gemma-4-31b-it:free",
                "attempts": 1,
                "fallback_reason": None,
                "status": "running",
                "error": "",
                "latency_ms": 0,
                "success": False,
            }
        ]

        with patch("interview_app_frontend.app.st.set_page_config"), patch(
            "interview_app_frontend.app.ensure_session_state"
        ), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ), patch("interview_app_frontend.components.request_log_panel.render_request_log_panel") as mock_log_panel:
            main()

        mock_log_panel.assert_not_called()

    def test_answer_evaluation_screen_is_info_only(self):
        st.session_state.clear()
        st.session_state.request_log = [
            {
                "timestamp": 0,
                "task": "answer_evaluation",
                "provider": "open-router",
                "model": "google/gemma-4-31b-it:free",
                "attempts": 1,
                "fallback_reason": None,
                "status": "running",
                "error": "",
                "latency_ms": 0,
                "success": False,
            }
        ]

        def _columns_mock(*args, **kwargs):
            return (MagicMock(), MagicMock())

        with patch("interview_app_frontend.components.answer_evaluation_screen.render_interview_sidebar") as mock_sidebar, patch(
            "interview_app_frontend.components.answer_evaluation_screen.render_shared_topbar"
        ) as mock_topbar, patch(
            "interview_app_frontend.components.answer_evaluation_screen.consume_answer_evaluation",
            return_value=None,
        ), patch("interview_app_frontend.components.answer_evaluation_screen.render_loading_indicator") as mock_loading, patch(
            "interview_app_frontend.components.answer_evaluation_screen.st.columns",
            side_effect=_columns_mock,
        ) as mock_columns, patch(
            "interview_app_frontend.components.answer_evaluation_screen.st.rerun"
        ), patch("interview_app_frontend.components.answer_evaluation_screen.st.markdown"):
            (getattr(render_answer_evaluation, "__wrapped__", render_answer_evaluation))()

        mock_columns.assert_called_once()
        mock_sidebar.assert_called_once()
        mock_topbar.assert_called_once()
        mock_loading.assert_called_once()
        assert mock_loading.call_args.args[0] == "Evaluation in progress"
        assert mock_loading.call_args.kwargs.get("compact") is True

    def test_query_param_route_is_only_applied_once(self):
        st.session_state.clear()
        st.session_state.current_screen = "welcome"
        st.session_state.has_active_session = False

        with patch.object(app_module.st, "query_params", {"screen": "question"}), patch(
            "interview_app_frontend.app.st.set_page_config"
        ), patch("interview_app_frontend.app.ensure_session_state"), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ):
            main()

        self.assertEqual(st.session_state.current_screen, "question")

        st.session_state.current_screen = "feedback"
        with patch.object(app_module.st, "query_params", {"screen": "question"}), patch(
            "interview_app_frontend.app.st.set_page_config"
        ), patch("interview_app_frontend.app.ensure_session_state"), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ):
            main()

        self.assertEqual(st.session_state.current_screen, "feedback")

    def test_main_cleans_bad_widget_state_before_rendering(self):
        st.session_state.clear()
        st.session_state.role_selectbox = "Backend Engineer"
        st.session_state[SETUP_WIDGET_KEYS["setup_role"]] = "Backend Engineer"
        st.session_state.setup_tech_stack_control = ["Java / Spring Boot"]

        with patch("interview_app_frontend.app.st.set_page_config"), patch(
            "interview_app_frontend.app.ensure_session_state"
        ), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ):
            main()

        self.assertNotIn("role_selectbox", st.session_state)
        self.assertNotIn("setup_role_selectbox", st.session_state)
        self.assertNotIn(SETUP_WIDGET_KEYS["setup_role"], st.session_state)
        self.assertNotIn(SETUP_WIDGET_KEYS["setup_persona"], st.session_state)
        self.assertNotIn(SETUP_WIDGET_KEYS["setup_difficulty"], st.session_state)
        self.assertNotIn(SETUP_WIDGET_KEYS["setup_response_style"], st.session_state)
        self.assertNotIn(SETUP_WIDGET_KEYS["setup_cv_mode"], st.session_state)
        self.assertNotIn("setup_tech_stack_control", st.session_state)

    def test_question_screen_renders_answer_layout(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Python"
        st.session_state.setup_job_description = "Backend role"
        with patch(
            "interview_app_backend.services.question_generation_job.get_next_question_for_session",
            return_value="A user reports that a page in your application is slow due to API latency. How would you investigate and improve performance?",
        ):
            start_interview()
        self._wait_for_generation()

        with patch("interview_app_frontend.ui.screens.render_question_and_answer") as mock_render_question, patch(
            "interview_app_frontend.ui.screens.render_setup"
        ), patch("interview_app_frontend.ui.screens.render_welcome"):
            from interview_app_frontend.ui.screens import render_screen

            render_screen()

        mock_render_question.assert_called_once()

    def test_welcome_with_active_session_routes_to_question(self):
        st.session_state.clear()
        st.session_state.current_screen = "welcome"
        st.session_state.has_active_session = True
        st.session_state.current_question_index = 1
        st.session_state.current_question = "A user reports that a page in your application is slow due to API latency. How would you investigate and improve performance?"

        with patch("interview_app_frontend.ui.screens.render_question_and_answer") as mock_render_question, patch(
            "interview_app_frontend.ui.screens.render_setup"
        ), patch("interview_app_frontend.ui.screens.render_welcome"):
            from interview_app_frontend.ui.screens import render_screen

            render_screen()

        mock_render_question.assert_not_called()

    def test_launch_flag_forces_question_screen(self):
        st.session_state.clear()
        st.session_state.current_screen = "welcome"
        st.session_state.has_active_session = False
        st.session_state.launch_question_view = True

        with patch("interview_app_frontend.ui.screens.render_question_and_answer") as mock_render_question, patch(
            "interview_app_frontend.ui.screens.render_setup"
        ), patch("interview_app_frontend.ui.screens.render_welcome"):
            from interview_app_frontend.ui.screens import render_screen

            render_screen()

        mock_render_question.assert_not_called()

    def test_sample_answer_screen_routes_from_feedback_view(self):
        st.session_state.clear()
        st.session_state.current_screen = "sample_answer"

        with patch("interview_app_frontend.ui.screens.render_sample_answer") as mock_render_sample, patch(
            "interview_app_frontend.ui.screens.render_setup"
        ), patch("interview_app_frontend.ui.screens.render_welcome"), patch(
            "interview_app_frontend.ui.screens.render_question_and_answer"
        ):
            from interview_app_frontend.ui.screens import render_screen

            render_screen()

        mock_render_sample.assert_called_once()

    def test_generating_question_screen_routes_to_preparing_view(self):
        st.session_state.clear()
        st.session_state.current_screen = "generating_question"

        with patch("interview_app_frontend.ui.screens.render_generating_question") as mock_render_generating, patch(
            "interview_app_frontend.ui.screens.render_setup"
        ), patch("interview_app_frontend.ui.screens.render_welcome"), patch(
            "interview_app_frontend.ui.screens.render_question_and_answer"
        ):
            from interview_app_frontend.ui.screens import render_screen

            render_screen()

        mock_render_generating.assert_called_once()

    def test_question_screen_renders_warning_banner(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Python"
        st.session_state.setup_job_description = "Backend role"
        with patch(
            "interview_app_backend.services.question_generation_job.get_next_question_for_session",
            return_value="Your API response time increased from 200ms to 800ms. How would you investigate and improve performance?",
        ):
            start_interview()
        self._wait_for_generation()
        st.session_state.job_description = "Added"
        st.session_state.cv_status = "Uploaded"

        with patch("interview_app_frontend.components.question_screen.st.markdown") as mock_markdown, patch(
            "interview_app_frontend.components.question_screen.st.text_area"
        ), patch("interview_app_frontend.components.question_screen.st.columns") as mock_columns, patch(
            "interview_app_frontend.components.question_screen.st.button"
        ), patch("interview_app_frontend.components.question_screen.st.container") as mock_container:
            mock_columns.side_effect = lambda spec, **kwargs: tuple(MagicMock() for _ in range(len(spec)))
            mock_container.return_value.__enter__.return_value = MagicMock()
            mock_container.return_value.__exit__.return_value = False
            render_question_and_answer()

        rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
        self.assertIn("question-warning", rendered_html)
        self.assertNotIn("This application supports interview preparation only.", rendered_html)
        self.assertIn("setup-sidebar-status", rendered_html)
        self.assertIn("setup-sidebar--active", rendered_html)
        mock_container.assert_called_once_with(border=True, key="question_answer_card")

    def test_start_interview_uses_llm_generated_question(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Built APIs and improved performance."
        st.session_state.setup_job_description = "Backend role focused on APIs and performance."

        def _submit_sync(func, payload):
            future = Future()
            future.set_result(func(payload))
            return future

        with patch("interview_app_backend.services.question_generation_job.get_next_question_for_session", return_value={
            "questions": [
                {
                    "sequence_order": 1,
                    "question": "How would you improve an API under load?",
                    "question_type": "jd_based",
                    "focus_area": "performance",
                    "source_basis": {"cv_terms_used": ["API"], "jd_terms_used": ["backend"], "gap_used": None},
                    "difficulty_level": "Medium",
                    "what_interviewer_is_testing": ["Performance investigation"],
                }
            ],
            "meta": {
                "total_questions": 1,
                "distribution": {
                    "cv_based": 0,
                    "jd_based": 1,
                    "behavioural": 0,
                    "deep_dive": 0,
                    "gap_targeted": 0,
                },
            },
        }), patch(
            "interview_app_backend.services.question_generation_job._EXECUTOR.submit",
            side_effect=_submit_sync,
        ):
            start_interview()
        self._wait_for_generation()

        self.assertEqual(st.session_state.current_question, "How would you improve an API under load?")
        self.assertEqual(st.session_state.question_meta["total_questions"], 1)
        self.assertEqual(st.session_state.question_meta["distribution"]["jd_based"], 1)

    def test_setup_screen_start_button_uses_validation_callback(self):
        st.session_state.clear()

        with patch("interview_app_frontend.components.shell.render_interview_sidebar"), patch(
            "interview_app_frontend.components.shell.render_shared_topbar"
        ), patch("interview_app_frontend.components.shell.st.columns") as mock_columns, patch(
            "interview_app_frontend.components.shell.st.markdown"
        ), patch("interview_app_frontend.components.shell.st.segmented_control") as mock_segmented_control, patch(
            "interview_app_frontend.components.shell.st.text_area"
        ), patch("interview_app_frontend.components.shell.st.slider"), patch(
            "interview_app_frontend.components.shell.st.button"
        ) as mock_button:
            mock_columns.side_effect = lambda spec, **kwargs: tuple(MagicMock() for _ in range(len(spec)))
            from interview_app_frontend.components.shell import render_setup

            render_setup()

        button_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Start Interview"]
        self.assertTrue(button_calls)
        self.assertEqual(button_calls[0].kwargs.get("key"), "setup_start_interview")
        self.assertIsNotNone(button_calls[0].kwargs.get("on_click"))
        self.assertFalse(button_calls[0].kwargs.get("disabled", True))
        self.assertTrue(mock_segmented_control.called)
        role_calls = [call for call in mock_segmented_control.call_args_list if call.kwargs.get("key") == SETUP_WIDGET_KEYS["setup_role"]]
        self.assertTrue(role_calls)
        self.assertEqual(role_calls[0].kwargs.get("default"), "Backend Engineer")
        self.assertEqual(role_calls[0].kwargs.get("label_visibility"), "collapsed")
        expected_keys = {
            SETUP_WIDGET_KEYS["setup_role"],
            SETUP_WIDGET_KEYS["setup_persona"],
            SETUP_WIDGET_KEYS["setup_cv_mode"],
            SETUP_WIDGET_KEYS["setup_difficulty"],
            SETUP_WIDGET_KEYS["setup_response_style"],
        }
        self.assertTrue(expected_keys.issubset({call.kwargs.get("key") for call in mock_segmented_control.call_args_list}))

    def test_question_submit_button_stays_enabled_for_short_draft(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Python"
        st.session_state.setup_job_description = "Backend role"
        with patch(
            "interview_app_backend.services.question_generation_job.get_next_question_for_session",
            return_value="Question",
        ):
            start_interview()
        self._wait_for_generation()
        st.session_state.answer = "Short draft answer that is still shorter than the feedback threshold but should not disable the button"

        with patch("interview_app_frontend.components.question_screen.st.markdown"), patch(
            "interview_app_frontend.components.question_screen.st.text_area"
        ), patch("interview_app_frontend.components.question_screen.st.columns") as mock_columns, patch(
            "interview_app_frontend.components.question_screen.st.button"
        ) as mock_button, patch("interview_app_frontend.components.question_screen.st.container") as mock_container:
            mock_columns.side_effect = lambda spec, **kwargs: tuple(MagicMock() for _ in range(len(spec)))
            mock_container.return_value.__enter__.return_value = MagicMock()
            mock_container.return_value.__exit__.return_value = False
            render_question_and_answer()

        submit_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Submit Answer"]
        self.assertTrue(submit_calls)
        self.assertFalse(submit_calls[0].kwargs.get("disabled", False))

    def test_question_submit_button_is_disabled_when_answer_is_empty(self):
        st.session_state.clear()
        st.session_state.setup_role = "Backend Engineer"
        st.session_state.setup_persona = "Strict"
        st.session_state.setup_difficulty = "Medium"
        st.session_state.setup_response_style = "Concise"
        st.session_state.setup_cv_content = "Python"
        st.session_state.setup_job_description = "Backend role"
        with patch(
            "interview_app_backend.services.question_generation_job.get_next_question_for_session",
            return_value="Question",
        ):
            start_interview()
        self._wait_for_generation()
        st.session_state.answer = ""

        with patch("interview_app_frontend.components.question_screen.st.markdown"), patch(
            "interview_app_frontend.components.question_screen.st.text_area"
        ), patch("interview_app_frontend.components.question_screen.st.columns") as mock_columns, patch(
            "interview_app_frontend.components.question_screen.st.button"
        ) as mock_button, patch("interview_app_frontend.components.question_screen.st.container") as mock_container:
            mock_columns.side_effect = lambda spec, **kwargs: tuple(MagicMock() for _ in range(len(spec)))
            mock_container.return_value.__enter__.return_value = MagicMock()
            mock_container.return_value.__exit__.return_value = False
            render_question_and_answer()

        submit_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Submit Answer"]
        self.assertTrue(submit_calls)
        self.assertTrue(submit_calls[0].kwargs.get("disabled", False))


if __name__ == "__main__":
    unittest.main()
