# Interview Practice App

## Architecture

- `interview_app_frontend/` contains Streamlit screens, components, and session state.
- `interview_app_backend/` contains services, LLM wrappers, CV processing, and models.
- `shared/` contains common constants, enums, and types.
- `config/` contains runtime settings and prompt configuration.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Model Configuration

Set `MODEL_NAME` in `.env`:

- Question generation now prefers `google/gemma-4-31b-it:free`, then `google/gemma-3-12b-it:free`.
- Evaluation uses the same Google-only free ranking, but stays free-only and falls back to a controlled degraded result if all models fail.
- `openai/gpt-5-nano` is kept only as a generation safety net.

**Why these models?** The app requires strict JSON output for structured prompts (question generation, evaluation, feedback). Free Gemini models keep the workspace on the OpenRouter free tier.

## Folder Responsibilities

- `app.py` remains a root launcher for convenience.
- `interview_app_frontend/app.py` is the Streamlit entry point.
- UI code stays in `interview_app_frontend/` and does not call LLMs directly.
- Business logic stays in `interview_app_backend/services/`.
- Prompts stay in `interview_app_backend/llm/prompts/`.
