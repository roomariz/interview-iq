from collections.abc import Callable
from html import escape

import streamlit as st


def render_question_panel(
    *,
    question_index: int,
    total_questions: int,
    role: str,
    difficulty: str,
    persona: str,
    current_question: str,
    banner_message: str,
    current_answer: str,
    submit_disabled: bool,
    input_disabled: bool = False,
    max_answer_length: int,
    on_back: Callable[[], None],
    on_submit: Callable[[], None],
    on_clear: Callable[[], None],
) -> None:
    st.markdown(
        f"""
        <style>
        .question-card-inline {{
            border: 1px solid #ced8e7;
            border-radius: 10px;
            overflow: hidden;
            background: #ffffff;
            width: 100%;
        }}
        .question-card-inline__header {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            min-height: 56px;
            padding: 0.6rem 0.95rem;
            background: #f6f8ff;
            border-bottom: 1px solid #d7deea;
        }}
        .question-card-inline__icon {{
            width: 30px;
            height: 30px;
            border-radius: 7px;
            background: #2454c8;
            color: #ffffff;
            display: inline-grid;
            place-items: center;
            flex: 0 0 auto;
            font-size: 0.82rem;
            font-weight: 800;
        }}
        .question-card-inline__title {{
            margin: 0;
            color: #2454c8;
            font-size: 1.22rem;
            line-height: 1.08;
            font-weight: 800;
        }}
        .question-card-inline__body {{
            padding: 0.78rem 0.95rem 0.86rem;
            width: 100%;
        }}
        .question-card-inline__meta {{
            display: flex;
            flex-wrap: nowrap;
            align-items: center;
            gap: 0.4rem 0.7rem;
            color: #2454c8;
            font-size: 0.88rem;
            white-space: nowrap;
            overflow-x: auto;
        }}
        .question-card-inline__meta strong,
        .question-card-inline__meta span {{
            color: #2454c8;
        }}
        .question-card-inline__meta span {{
            color: #14224b;
        }}
        .question-card-inline__divider {{
            width: 1px;
            height: 1.1rem;
            background: #2454c8;
            margin: 0 0.2rem;
        }}
        .question-card-inline__question {{
            margin-top: 0.7rem;
            padding-top: 0.72rem;
            border-top: 1px solid #e5eaf2;
            color: #1b2b54;
            font-size: 1.28rem;
            line-height: 1.26;
            font-weight: 800;
            width: 100%;
            max-width: none;
        }}
        .question-count {{
            margin: 0.25rem 0 0.08rem;
            padding: 0.1rem 0;
        }}
        .question-answer-card__title {{
            font-size: 1.22rem;
            line-height: 1.1;
        }}
        [data-testid="stElementContainer"].st-key-question_back button,
        [data-testid="stElementContainer"].st-key-question_submit_answer button,
        [data-testid="stElementContainer"].st-key-question_clear_answer button {{
            min-height: 40px;
            padding: 0.45rem 0.75rem;
        }}
        [data-testid="stTextArea"] textarea[aria-label="Write your answer here..."] {{
            min-height: 140px !important;
        }}
        @media (max-height: 860px) {{
            .question-card-inline__header {{
                min-height: 52px;
                padding: 0.52rem 0.9rem;
            }}
            .question-card-inline__body {{
                padding: 0.68rem 0.9rem 0.76rem;
            }}
            .question-card-inline__question {{
                margin-top: 0.58rem;
                padding-top: 0.62rem;
                font-size: 1.18rem;
                line-height: 1.22;
            }}
            .question-answer-card__title {{
                font-size: 1.14rem;
            }}
            .question-warning {{
                margin-bottom: 0.72rem;
                padding: 0.82rem 0.92rem;
            }}
            [data-testid="stTextArea"] textarea[aria-label="Write your answer here..."] {{
                min-height: 128px !important;
            }}
        }}
        </style>
        <section class="question-card-inline">
            <div class="question-card-inline__header">
                <span class="question-card-inline__icon">★</span>
                <h1 class="question-card-inline__title">Question {question_index} of {total_questions}</h1>
            </div>
            <div class="question-card-inline__body">
                <div class="question-card-inline__meta">
                    <span><strong>Role:</strong> <span>{escape(role)}</span></span>
                    <span class="question-card-inline__divider" aria-hidden="true"></span>
                    <span><strong>Difficulty:</strong> <span>{escape(difficulty)}</span></span>
                    <span class="question-card-inline__divider" aria-hidden="true"></span>
                    <span><strong>Persona:</strong> <span>{escape(persona)}</span></span>
                    <span class="question-card-inline__divider" aria-hidden="true"></span>
                    <span><strong>Focus:</strong> <span>Performance Optimisation</span></span>
                </div>
                <div class="question-card-inline__question">{escape(current_question)}</div>
                <div class="question-card-inline__question-raw" style="display:none;">{escape(current_question)}</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    answer_card = st.container(border=True, key="question_answer_card")
    with answer_card:
        st.markdown("### Your Answer")
        if banner_message:
            st.warning(banner_message)
        answer_input = st.text_area(
            "Write your answer here...",
            height=140,
            max_chars=max_answer_length,
            key="answer",
            label_visibility="collapsed",
            placeholder="Write your answer here...",
            disabled=input_disabled,
        )
        st.markdown(f'<div class="question-answer-raw" style="display:none;">{escape(answer_input)}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="question-count">Character count: {len(current_answer)} / {max_answer_length}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="question-actions-divider" aria-hidden="true"></div>', unsafe_allow_html=True)
        action_back, col_submit, col_clear = st.columns([0.92, 1.9, 1], gap="small")
        with action_back:
            st.button(
                "Back",
                key="question_back",
                help="Return to the setup screen without clearing your selections",
                on_click=on_back,
                use_container_width=True,
                disabled=input_disabled,
            )
        with col_submit:
            st.button(
                "Submit Answer",
                disabled=submit_disabled,
                key="question_submit_answer",
                on_click=on_submit,
                use_container_width=True,
            )
        with col_clear:
            st.button(
                "Clear",
                disabled=input_disabled,
                key="question_clear_answer",
                on_click=on_clear,
                use_container_width=True,
            )
