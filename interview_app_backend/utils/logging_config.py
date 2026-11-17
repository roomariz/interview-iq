import logging
import sys
from interview_app_backend.utils.private_logging import install, PrivateFields, DiagnosticFormatter


APP_LOGGER = "app"
LLM_LOGGER = "llm"


def setup_logging() -> None:
    install()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("streamlit.runtime.scriptrunner").setLevel(logging.ERROR)
    logging.getLogger("streamlit.runtime.context").setLevel(logging.ERROR)

    formatter = DiagnosticFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(PrivateFields())

    app_logger = logging.getLogger(APP_LOGGER)
    app_logger.setLevel(logging.INFO)
    app_logger.handlers.clear()
    app_logger.addHandler(handler)

    llm_logger = logging.getLogger(LLM_LOGGER)
    llm_logger.setLevel(logging.INFO)
    llm_logger.handlers.clear()
    llm_logger.addHandler(handler)

    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    security = logging.getLogger("interview.security")
    security.setLevel(logging.INFO)
    security.handlers[:] = [handler]
    security.propagate = False


def get_app_logger() -> logging.Logger:
    return logging.getLogger(APP_LOGGER)


def get_llm_logger() -> logging.Logger:
    return logging.getLogger(LLM_LOGGER)
