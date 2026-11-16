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

