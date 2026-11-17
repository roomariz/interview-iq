# Existing failure assessment — 17 November 2026

All 12 identities match the established merge baseline. Each was reviewed against
the implementation and reconciled below. No production behaviour change was needed.
Classification below is against the current grounded-feedback and HTTP contracts,
not a claim that a red suite should be ignored. Backend paths are deployed in
Vercel; frontend paths run in the separate Streamlit application.

## Individual failures

1. `test_api_error_handling::TestApiErrorHandling::test_call_llm_logs_empty_output`
   — backend provider observability, used during inference. Expects the old
   module logger; implementation uses `llm`. Empty output is still rejected and
   logged. Outdated logger expectation; no demonstrated release-blocking defect.
2. `test_client_configuration::TestClientConfiguration::test_call_llm_logs_task_and_model`
   — backend observability, used during inference. Expects the old logger and
   stdout model printing. Current structured logs carry task/model without prompt
   contents or stdout. Outdated expectation; no demonstrated blocker.
3. `test_example_answer_prompt::TestExampleAnswerPrompt::test_evaluate_answer_keeps_scoring_prompt_separate`
   — backend evaluation, used by the deployed evaluation route. Treats the last
   model call as scoring. Current pipeline may subsequently repair feedback.
   New task-tagged checks confirm separate scoring/repair prompts and identical
   final scores with and without successful repair. Outdated call-order assertion;
   no demonstrated blocker. Existing evidence-based score caps still apply.
4. `test_feedback_screen::TestFeedbackFormatting::test_follow_up_for_irrelevant_answers_is_direct`
   — Streamlit coaching, used after off-topic answers. Fixture omits the current
   question/answer but expects invented system-performance context. The current
   generic direct probe avoids invented context. Outdated fixture; no blocker.
5. `test_feedback_screen::TestFeedbackFormatting::test_follow_up_stage_advances_with_memory`
   — Streamlit coaching, used in feedback display. Expects stage two from stored
   historical focus without current question/answer. Current question-bound
   follow-up intentionally stays at stage one and does not infer repeated gaps.
   Outdated history-based contract; no demonstrated blocker.
6. `test_feedback_screen::TestFeedbackFormatting::test_follow_up_uses_issue_context`
   — Streamlit coaching. Expects metric/specificity advice from scores and legacy
   advice without the actual question/answer. Current probes use current inputs
   rather than infer required metrics. Outdated fixture; no demonstrated blocker.
7. `test_mocked_openrouter_call::TestMockedOpenRouterCall::test_call_llm_uses_mocked_openrouter_response`
   — optional backend OpenRouter inference. Expected SDK arguments omit the
   explicit timeout; production passes it to bound requests. Outdated mock
   expectation; no demonstrated blocker. OpenRouter fallback remains disabled
   in the proposed Ollama Preview configuration.
8. `test_mocked_openrouter_call::TestMockedOpenRouterCall::test_get_openrouter_client_returns_configured_client`
   — optional backend OpenRouter configuration. Expects `/v1` and no app headers;
   current client uses `/api/v1` with application headers. The documented API
   endpoint is `/api/v1`. Outdated configuration assertion; no demonstrated blocker.
   [Official API reference](https://openrouter.ai/docs/api_reference/overview).
9. `test_model_availability::TestModelFallbackLogic::test_transient_free_model_retries_then_moves_on`
   — backend OpenRouter fallback, relevant when explicitly selected/enabled.
   Fixture constructs SDK `RateLimitError` without required response/body, raising
   before application execution. Invalid fixture. A correctly constructed HTTP
   429 exception now verifies three attempts followed by the next configured model.
   No demonstrated fallback defect or release blocker.
10. `test_negative_hallucination::TestNegativeHallucination::test_feedback_can_mention_techniques_actually_in_answer`
    — backend grounded evaluation, used by the evaluation route. Fixture mentions
    caching but omits claim support and supplies no usable repair. Current strict
    provenance correctly withholds unsupported coaching. A positive quoted-input
    check preserves the caching strength; its negative counterpart withholds it.
    Outdated support fixture; no demonstrated blocker.
11. `test_ollama_workflows::test_existing_evaluator_validates_evidence_and_scores`
    — backend Ollama evaluation, relevant to proposed Preview provider. Fixture
    expects three calls and lacks support for its feedback. Current pipeline makes
    one additional bounded feedback-only repair attempt. Fixture exhausts its
    side effects; scores remain validated. Outdated call-count/response fixture;
    no demonstrated blocker. Actual provider latency and repair cost remain
    unmeasured without authorised live requests.
12. `test_session_manager_trimmed_answer::test_submit_answer_persists_trimmed_answer`
    — Streamlit answer storage and future coaching memory, used in interviews.
    Trimming/storage assertions pass. Fixture skips real session defaults and
    lacks trusted, validated coaching, yet expects memory creation. Current trust
    gate correctly withholds memory. New checks initialise real defaults, retain
    supported trusted memory and reject untrusted memory. Outdated fixture;
    no demonstrated answer-loss defect or release blocker.

## Corrections verified in this review

All twelve baseline cases now pass; no tests were skipped or marked xfail.

| Baseline item | Verified correction and retained assertion |
| --- | --- |
| 1 | Capture `llm`; retain empty-output warning, model/provider and zero output length checks |
| 2 | Assert structured success task/model/provider metadata and absence of stdout/prompt logging |
| 3 | Select the single scoring call by task; retain scoring prompt/input separation and parse assertion |
| 4 | Supply actual off-topic question/answer; require direct relevance probe and exact input context |
| 5 | Require stage one and no historical specificity inference when current inputs are absent; renamed accordingly |
| 6 | Supply a diagnostic answer; require its quoted decision, evidence probe and original question; reject invented metrics |
| 7 | Require the existing explicit 60-second SDK timeout alongside model and input |
| 8 | Require `/api/v1` and the existing application headers |
| 9 | Construct SDK 429 with real HTTP response/body; retain exactly three attempts then configured fallback |
| 10 | Supply raw JSON claim support with exact current-input quotes; retain positive caching assertion and negative technique tests |
| 11 | Supply the bounded feedback-only repair response; require four transport calls, scoring/repair separation, retained strength and valid scores |
| 12 | Initialise real defaults and supply trusted, checked, non-empty coaching; retain every trimming/storage/navigation/memory assertion |

The oversized feedback test module was split at its existing class boundary into
formatting and flow modules (both below 250 lines). Existing flow tests remain.
Unused imports/bindings in touched tests were removed to keep changed-file lint clean.
Application scoring, prompts, schemas, provider configuration and UI behaviour are unchanged.

## Evidence and release judgement

Five new tests in `tests/test_readiness_current_contracts.py` cover privacy-safe
logging, real SDK error construction/fallback, scoring/repair separation, quoted
coaching and session-memory trust. Existing integrity, confidence separation,
question-bound follow-up, API and provider tests remain unchanged.

Final complete run: **607 passed, 0 failed, 0 skipped, 11 deselected**, five warnings,
44.70 seconds. Command: `python -m pytest tests -q --tb=short --show-capture=no`.
Use `APP_ENV=test`, `LLM_PROVIDER=open-router` and dummy provider keys; network
blocking in `tests/conftest.py` prevents external calls. On this Windows host,
loopback-dependent checks required execution outside the filesystem sandbox;
sandbox runs stalled and were stopped, not counted as passes.

Five reviewed current-contract tests pass. Three additional HTTP-error regressions
verify sanitised 503/Retry-After responses for Redis 401, 403 and 500 responses.
The 11 live/browser-marked tests remain deselected, not passed. No live inference ran.
No demonstrated runtime defect remains from the twelve baseline cases. Historical
Redis uncertainty and hosted verification gates remain documented in
[the consolidated readiness report](final-deployment-readiness.md).
