import streamlit as st
import streamlit.components.v1 as components

from config.settings import LLM_PROVIDER, MODEL_NAME
from interview_app_frontend.components.shell import SETUP_WIDGET_KEYS
from interview_app_frontend.ui.screens import render_screen
from interview_app_frontend.state.session_manager import ensure_session_state
from interview_app_frontend.utils.styles import inject_styles
from interview_app_backend.utils.logging_config import setup_logging, get_app_logger


LOGGER = get_app_logger()
ANSWER_PASTE_FIX = """
<script>
(function () {
    const selector = 'textarea[aria-label="Write your answer here..."]';

    const patchTextarea = () => {
        try {
            const parentDoc = window.parent && window.parent.document;
            if (!parentDoc) {
                return;
            }

            parentDoc.querySelectorAll(selector).forEach((textarea) => {
                textarea.removeAttribute("readonly");
                textarea.readOnly = false;
                textarea.style.pointerEvents = "auto";
            });
        } catch (error) {
            console.debug("Answer textarea paste fix skipped:", error);
        }
    };

    patchTextarea();

    try {
        const parentDoc = window.parent && window.parent.document;
        if (!parentDoc || !parentDoc.body) {
            return;
        }

        const observer = new MutationObserver(patchTextarea);
        observer.observe(parentDoc.body, { subtree: true, childList: true, attributes: true });
        window.setTimeout(() => observer.disconnect(), 5000);
    } catch (error) {
        console.debug("Answer textarea observer unavailable:", error);
    }
})();
</script>
"""


def clean_widget_state() -> None:
    keys_to_clean = [
        "role_selectbox",
        "setup_role_selectbox",
        "setup_role_tabs",
        "setup_persona_tabs",
        "setup_difficulty_tabs",
        "setup_response_style_tabs",
        "setup_cv_mode_tabs",
        "setup_tech_stack_control",
        *SETUP_WIDGET_KEYS.values(),
    ]
    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]


def _apply_route_from_query_params() -> None:
    if st.session_state.get("_query_route_applied", False):
        return
    screen = st.query_params.get("screen")
    if screen:
        st.session_state.current_screen = screen
        st.session_state._query_route_applied = True


def main() -> None:
    setup_logging()
    LOGGER.info("APP_START", extra={"version": "1.0"})
    st.set_page_config(page_title="InterviewIQ", layout="wide")
    clean_widget_state()
    ensure_session_state()
    LOGGER.info("Resolved LLM provider: %s model: %s", LLM_PROVIDER, MODEL_NAME)
    _apply_route_from_query_params()
    inject_styles()
    if st.session_state.get("current_screen") == "question":
        components.html(ANSWER_PASTE_FIX, height=0, width=0)
    render_screen()


if __name__ == "__main__":
    main()
