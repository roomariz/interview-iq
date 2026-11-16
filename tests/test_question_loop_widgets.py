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

