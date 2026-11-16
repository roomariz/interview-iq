"""Display defaults only. Provider configuration is resolved by FastAPI."""

MODEL_NAME = ""
LLM_PROVIDER = "backend"


def is_free_model(model):
    return str(model).endswith(":free")


def get_question_count(model):
    return 3 if not model or is_free_model(model) else 5
