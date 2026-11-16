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
    def test_main_logs_resolved_model_name_on_startup(self):
        st.session_state.clear()
        with patch("interview_app_frontend.app.st.set_page_config"), patch(
            "interview_app_frontend.app.ensure_session_state"
        ), patch("interview_app_frontend.app.inject_styles"), patch(
            "interview_app_frontend.app.render_screen"
        ), patch("interview_app_frontend.app.LOGGER.info") as mock_log:
            main()

        mock_log.assert_any_call("Resolved LLM provider: %s model: %s", app_module.LLM_PROVIDER, app_module.MODEL_NAME)


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
            with self.assertRaisesRegex(RuntimeError, "duplicate_previous_question"):
                get_next_question_for_session(
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
