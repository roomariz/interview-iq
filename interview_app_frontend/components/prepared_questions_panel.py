from html import escape
from typing import Any

import streamlit as st


def _question_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("question", "")).strip()
    return str(item).strip()


def _question_order(item: object, fallback: int) -> int:
    if isinstance(item, dict):
        try:
            order = int(item.get("sequence_order", fallback))
            return order if order > 0 else fallback
        except (TypeError, ValueError):
            return fallback
    return fallback


def render_prepared_questions_panel(prepared_questions: list[object] | None, question_meta: dict[str, object] | None = None) -> None:
    ordered_items = [item for item in (prepared_questions or []) if _question_text(item)]
    questions = [(_question_order(item, index), _question_text(item)) for index, item in enumerate(ordered_items, start=1)]
    if not questions:
        return

    meta = question_meta if isinstance(question_meta, dict) else {}
    total_questions = meta.get("total_questions") if isinstance(meta.get("total_questions"), int) else len(questions)

    st.markdown(
        """
        <style>
        .prepared-questions-card { border: 1px solid #dbe3f0; border-radius: 14px; background: #fbfcff; padding: 0.9rem 1rem; margin: 0 0 0.9rem; }
        .prepared-questions-card__title { margin: 0 0 0.4rem; font-size: 1.02rem; font-weight: 800; color: #1b2b54; }
        .prepared-questions-card__list { margin: 0; padding-left: 1.15rem; color: #2b3d6b; }
        .prepared-questions-card__list li { margin-bottom: 0.35rem; line-height: 1.34; }
        .prepared-questions-card__meta { margin-bottom: 0.35rem; color: #5b6b89; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <section class="prepared-questions-card">
            <div class="prepared-questions-card__title">Prepared question set</div>
            <div class="prepared-questions-card__meta">Review these {total_questions} scenarios before answering the live prompt.</div>
            <ol class="prepared-questions-card__list">
                {''.join(f'<li>{escape(question)}</li>' for _, question in questions)}
            </ol>
        </section>
        """,
        unsafe_allow_html=True,
    )
