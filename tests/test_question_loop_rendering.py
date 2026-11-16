from question_loop_support import (  # noqa: F401
    QuestionLoopTestCase,
    sleep,
    time,
    patch,
    Future,
    st,
    MagicMock,
    app_module,
    main,
    SETUP_WIDGET_KEYS,
    poll_question_generation,
    render_answer_evaluation,
    render_question_and_answer,
    start_interview,
    get_next_question_for_session,
)


class TestFullQuestionLoop(QuestionLoopTestCase):
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

        def _submit_sync(func, payload, generator):
            future = Future()
            future.set_result(func(payload, generator))
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

