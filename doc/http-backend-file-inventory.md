# HTTP backend file inventory

All paths are relative to the repository root. No dependencies were added and no
provider configuration, scoring weights or prompt text was changed. Pure helper
and UI extractions keep changed files below 250 lines and prevent frontend imports
from loading provider configuration. Backend compatibility exports are retained.

## Created

- `api/errors.py`
- `api/interview.py`
- `api/security.py`
- `doc/http-backend-file-inventory.md`
- `doc/http-backend-integration.md`
- `doc/http-backend-test-results.md`
- `interview_app_frontend/components/welcome_screen.py`
- `interview_app_frontend/services/api_client.py`
- `interview_app_frontend/services/settings.py`
- `interview_app_frontend/state/question_generation_job.py`
- `interview_app_frontend/state/session_feedback.py`
- `interview_app_frontend/state/session_helpers.py`
- `interview_app_frontend/state/session_navigation.py`
- `shared/api_contracts.py`
- `shared/feedback_guards.py`
- `shared/interview_context.py`
- `shared/question_followup.py`
- `shared/question_topics.py`
- `shared/scoring.py`
- `shared/trust_defaults.py`
- `tests/legacy_ui_http_support.py`
- `tests/test_interview_api.py`
- `tests/test_interview_api_client.py`
- `tests/test_backend_llm_integration.py`
- `tests/test_local_streamlit_backend.py`
- `tests/test_backend_workflow.py`

## Modified

- `.env.example`
- `AGENTS.md`
- `api/index.py`
- `doc/developer-manual.md`
- `doc/manual.md`
- `doc/test-manual.md`
- `interview_app_backend/llm/prompts/question_generation.py`
- `interview_app_backend/services/evaluation_rules.py`
- `interview_app_backend/services/feedback_integrity.py`
- `interview_app_backend/services/question_followup.py`
- `interview_app_backend/services/question_similarity.py`
- `interview_app_backend/services/trust_defaults.py`
- `interview_app_frontend/app.py`
- `interview_app_frontend/components/generating_question_screen.py`
- `interview_app_frontend/components/shell.py`
- `interview_app_frontend/state/answer_evaluation_job.py`
- `interview_app_frontend/state/session_manager.py`
- `interview_app_frontend/state/state_schema.py`
- `interview_app_frontend/utils/feedback_model.py`
- `interview_app_frontend/utils/feedback_view.py`
- `tests/conftest.py`
- `tests/question_loop_support.py`

## Responsibilities

- `api/`: stateless service adapters, error contracts, authentication, request
  limits and per-instance abuse controls; existing health entrypoint retained.
- `interview_app_frontend/services/`: reusable validated HTTP client and
  provider-independent display defaults. No provider credentials are read here.
- Frontend state modules: copied HTTP jobs, existing session adaptation/storage,
  navigation, and independent mutable defaults. Screens and layout are unchanged.
- `shared/`: wire models and existing pure context, score, trust, topic and
  feedback helpers. Backend modules re-export moved helpers for compatibility.
- Tests: request/client/pipeline/session/render verification, explicit HTTP doubles
  for existing UI tests, and the existing external-network guard retained.
- Documentation: local commands, contract/workflow map, security limits,
  regression identities, Vercel review and required manual checks.

Ignored `.pytest_cache` snapshots, test reports and environment caches are local
verification artefacts and are not included in this inventory or intended for git.
No files were committed, pushed or deployed.
