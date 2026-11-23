# Free-model verification proposal

18 November 2026. **Updated proposal only; separate approval required to execute.**
Supersedes the Ollama/credit-consumption proposal. Maximum cash expenditure and
paid inference are both **US$0**, including use of existing purchased credits.
No billing activation, credit purchase, deployment or live inference performed.
Only public documentation/catalogue reads and one authenticated, read-only
OpenRouter key-metadata request succeeded. The full mocked suite was not repeated.

## Verified selection and limits

| Priority | Candidate | Evidence and decision |
| --- | --- | --- |
| 1 | `google/gemma-4-31b-it:free` through OpenRouter | Catalogue input/output prices both zero; endpoint listing contains Google AI Studio, status 0, advertised recent uptime 100%. Selected for proposed test. |
| 2 | `google/gemma-3-12b-it:free` through OpenRouter | Endpoint list empty at review. Not eligible for this run; do not silently substitute its paid ID. |
| 3 | Direct `gemini-3.5-flash-lite` | Google lists Standard free-tier input/output as free. Account/project tier and actual RPM/TPM/RPD not verified; conditional alternative only, never automatic fallback. |
| Excluded | Ollama Cloud, paid OpenRouter models, billed Gemini, xAI | No requests permitted, even using previously purchased credits or promotional paid-service balances. |

Sources checked 18 November 2026:
- [Preferred model endpoints](https://openrouter.ai/api/v1/models/google/gemma-4-31b-it:free/endpoints)
  and [model catalogue](https://openrouter.ai/api/v1/models).
- [Gemma 3 endpoint availability](https://openrouter.ai/api/v1/models/google/gemma-3-12b-it:free/endpoints).
- [OpenRouter free limits](https://openrouter.ai/collections/free-models): 20 RPM,
  50 RPD without the purchase threshold. No purchase to increase that limit.
- [Key metadata and limits](https://openrouter.ai/docs/api-reference/limits):
  existing key returned HTTP 200, `is_free_tier=true`, daily used 0, limit 50,
  remaining 50. No key/label disclosed. Deprecated `rate_limit` is not authoritative.
- [Gemini Standard pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite)
  and [project rate limits](https://ai.google.dev/gemini-api/docs/rate-limits):
  free pricing exists; actual quotas must be read from the intended AI Studio project.

Availability is metadata evidence, not proof of successful inference. Live model
authentication, capacity, JSON quality and latency remain untested. Recheck immediately
before any approved inference; upstream capacity can still reject an eligible call.
Do not interpret OpenRouter's free-tier account flag as a paid-model spending block.

## Decision gates

1. Prefer the exact Gemma 4 `:free` ID. Before inference, re-read catalogue,
   endpoint metadata and authenticated key quota without generation. Require an
   available zero-price endpoint and at least 12 daily requests remaining.
2. Verify provider-specific restrictions and free-route access metadata; record
   any unavailable provider-specific limits as unknown. Pace at most 10 attempts
   per rolling minute, below the published 20 RPM. A 429 stops the run; no retry
   storm, extra accounts, key rotation or paid route to evade restrictions.
3. If Gemma is unavailable, direct Gemini is eligible only after read-only evidence
   confirms the exact model is available to an existing Free-tier project with
   billing disabled, no trial-credit billing path, and sufficient active RPM/TPM/RPD.
   Read model availability without generation; do not enable billing to inspect it.
   Prepare its exact configuration and request separate approval before using it.
4. If neither option can be verified free and usable, **skip Free-model verification and continue
   the next mocked verification step with permanent mocked responses**. Record live verification as skipped,
   not passed. No suitable free option is not a reason to permit paid inference.

Gemma 4 currently meets public availability and account free-quota preparation
checks; therefore the proposed route is approval for Gemma, not a Free-model verification skip.
No the next mocked verification step scope is defined in repository documentation; if the skip condition is
reached, clarify its deliverables before unrelated implementation. Existing mocked
Preview remains available without any redeployment.

## Minimal isolated configuration after approval

Create at most one additional immutable protected Preview in existing personal
Hobby `roomas-projects/interviewiq-api-preview`, project
`prj_XjaA1iTvTn5AmtN8PCg551qeUGLg`. Deployment-scoped overrides only, via secure
input; never edit shared Preview variables, branch variables, aliases or domains.
Stop before upload if tooling cannot guarantee isolation. No push or frontend.

Keep mocked Preview `dpl_4ij7fmNGu3hb5ubUHrqrTMwk6wi9` and inert Production
`dpl_3r1dLtGUkZZ38R352icSbajiBTLx` unchanged. Their state is recorded Mock Preview update
evidence; freshly verify identity/protection before and after approved execution.
Keep All Deployments authentication, backend bearer and signed visitor tokens.
Use a separate backend-only artifact; never turn the permanent mock artifact live.

| Environment/configuration | Proposed value |
| --- | --- |
| APP_ENV / LLM_PROVIDER | `production` / `open-router` |
| IS_FREE_MODE | `true` |
| MODEL_NAME | `google/gemma-4-31b-it:free`; DEFAULT_MODEL is a code constant, not a new env setting |
| OPENROUTER_API_KEY | Existing eligible key, sensitive deployment-only override after approval |
| OLLAMA_API_KEY / GOOGLE_API_KEY / XAI_API_KEY | Absent/empty in this isolated deployment |
| OLLAMA_FALLBACK_TO_OPENROUTER | `false`; no Ollama calls allowed |
| BACKEND_API_SECRET / BACKEND_VISITOR_SIGNING_KEY | Independent random sensitive overrides, each at least 32 random bytes |
| BACKEND_RATE_BACKEND / BACKEND_RATE_NAMESPACE | Preserve `redis` / `interviewiq-mocked-preview` |
| UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN | Existing managed Redis, securely inherited |
| Visitor minute/day / global minute/day | Preserve `10` / `100` / `30` / `1000` |
| BACKEND_MAX_CONCURRENT / BACKEND_INGRESS_RATE_LIMIT | Preserve `4` / `300` |
| LLM_TIMEOUT / BACKEND_REQUEST_DEADLINE | Preserve `60` / `150` seconds |
| LIVE_VERIFICATION_RUN_ID / LIVE_VERIFICATION_EXPIRES_AT | Proposed overlay settings: fixed run ID, UTC expiry 30 minutes after activation |
| Runtime | Existing Python 3.12, fra1, function maximum 300s, pinned dependencies |

Use one stable synthetic visitor identity. Share existing Redis global quotas and
owned leases across both Previews; do not reset limits, counters or namespaces.
Budget/telemetry uses separate run-specific keys without deleting shared keys.
Retain fail-closed Redis behaviour, lease renewal and timeout ownership rules.

## Required isolated safety changes, not yet implemented

Current `config/settings.py` includes `openai/gpt-5-nano` in question/general
fallback chains. `IS_FREE_MODE=true` alone does not exclude those chains.
`get_fallback_chain` and provider dispatch must be constrained in the Free-model verification
artifact to the one verified free model for every task. Reject all other model
IDs/providers at the final outbound boundary, even if upstream code asks for them.
Keep repository defaults, scoring and other deployments unchanged.

Use the existing OpenRouter Responses SDK path and
[provider routing controls](https://openrouter.ai/docs/guides/routing/provider-selection):
`provider.only=['google-ai-studio']`, `allow_fallbacks=false`,
`max_price={prompt:0,completion:0}`, `require_parameters=true`.
No `models` fallback array, `openrouter/auto`, plugins, tools, search, BYOK or paid
cache features. Verify exact parameter forwarding with focused offline contract
tests. Unsupported required controls mean stop, never relax the price constraint.
Keep stateless `store=false` semantics and reject redirects/alternate origins.

Add a Redis atomic run ledger before every outbound model attempt, including
service retries and optional feedback repair. Enforce a kill switch, expiry,
per-case budgets and one outstanding live attempt. SDK internal retries stay zero.
A failed/ambiguous attempt consumes its reservation; never refund it for a replay.
Block extra calls even when service exception handling swallows a budget error.

Set Responses `max_output_tokens=2048`, including any reasoning, and bound fully
rendered input to 16,384 tokens using a validated matching tokenizer or conservative
bound, not character/4 estimates. Confirm translation to the advertised endpoint
`max_tokens` limit offline. Preserve complete inputs; reject excess rather than
truncate. Record numeric usage/cost privately before normal parsing discards it.
Run focused offline tests for these additions; no full mocked Preview rerun.

## Proposed single-run ceilings

| Resource | Maximum after explicit approval |
| --- | --- |
| Hosted HTTP requests | 20 including protection/schema/health checks; three live workflow requests |
| Outbound model attempts | 12 total: questions 3, evaluation 6, follow-up question 3 |
| Live workflow client replays | Zero |
| Provider request pace / outstanding attempts | At most 10 per rolling minute / one outstanding |
| Input/output per attempt | 16,384 / 2,048 tokens |
| Aggregate reserved input/output | 196,608 / 24,576 tokens; 221,184 combined |
| Metadata/audit HTTP reads during execution | At most 20, including preflight, postflight and generation audit |
| Verification data-plane HTTP requests | At most 52: 20 hosted + 12 inference + 20 metadata/audit |
| Execution window | 30 minutes; expiry fails closed |
| New cash / paid inference / purchased-credit consumption | **US$0 / US$0 / US$0** |

Twelve is a ceiling, not a target. No transfer of unused allocations between cases.
Use existing free hosting/Redis allowances only. Deployment control-plane requests
and internal Redis operations are separate; no load testing or unbounded polling.
A zero-price model must remain zero-price for each attempt. No budget increase,
credit purchase or alternative paid route on exhaustion. Any nonzero reported
inference cost is a failure requiring immediate stop and investigation.

## Exact small test plan

Synthetic fixtures: role `Backend Engineer`; CV `Built a synthetic Python REST API
with PostgreSQL and unit tests.`; JD `Maintain Python APIs, PostgreSQL queries and
reliable releases.` Medium, Neutral, Detailed; temperature 0.7.

The selected free profile advertises session limit 3 and question-list count 1,
unlike the old five-question Ollama proposal. Preserve that existing contract.

| Case | Expected result | Maximum model attempts |
| --- | --- | --- |
| F1 protection/auth | Health without/invalid platform bypass denied or redirected; valid platform auth reaches health. Context with missing/invalid backend bearer or missing/forged/expired visitor token returns 401. | 0 |
| F2 input schema | Authenticated question count 5 instead of 1, and evaluation answer `short`, each return 422 with no model call or work-quota debit. | 0 |
| F3 context | Valid synthetic context returns provider open-router, exact free model, session limit 3 and question-list count 1. | 0 |
| F4 authentication/questions | One question request, count 1: authenticated upstream success, one grounded question, valid JSON and live trace for the exact free model/provider. Local safe fallback is not a live pass. | 3 |
| F5 evaluation | One evaluation with fixed question/answer below: valid evidence/scoring JSON, five 0–10 dimensions, grounded coaching, valid trust/decision and question-bound follow-up. Free profile skips reference/similarity calls. | 6 |
| F6 follow-up generation | One question request, type follow_up, count 1, previous_questions containing F5 question; append synthetic F5 answer to CV context. One grounded, non-duplicate question with live trace. | 3 |
| F7 faults, offline only | Inject malformed/incomplete JSON, wrong count/schema, out-of-range scores, 401/403/402/429/5xx, timeout and connection failure. Sanitised errors; no paid/fallback egress, no invented live success. | 0 |
| F8 controls, offline only | Attempt paid IDs, Ollama egress, alternate provider, nonzero catalogue prices, expired run, Redis outage and races for last reservation. All fail closed. Verify retry bounds, usage capture and logs without secrets. | 0 |
| F9 close | Health/protection and original deployment identity rechecks; inspect numeric usage, free quota and zero cost; close run. | 0 |

F5 question: `A Python API becomes slow after a release. How would you diagnose
and recover it safely?`
F5 answer: `I would compare latency and error rates before and after the release,
inspect traces and slow PostgreSQL queries, and check connection pool saturation.
I would roll back if the release is implicated and verify recovery with the same
metrics before testing a fix under representative load.`

Evaluation follow-up is currently grounded locally; F6 separately verifies live
question generation. No standalone follow-up endpoint exists. Fault injection
stays offline; no remotely selectable mock/fault mode is added.

## Measurement, rollback and remaining risks

Record case/attempt IDs, model/provider, HTTP status, monotonic latency, retry
count/delay, validation/fallback verdict, reserved/actual input/output/reasoning
usage and cost. Keep numeric telemetry private and synthetic output artifacts
local/ignored. Never log credentials, headers, prompts, answers or reasoning text.
Use response usage plus bounded authenticated generation-detail reads where needed;
compare pre/post key daily counts and usage. Missing cost/usage is unknown, not zero.
No new inference after unknown/nonzero cost until resolved; no automatic replay.
Report each latency and median/range, not an unsupported p95; retain the 150s
aggregate deadline. Non-streaming calls do not establish time-to-first-token.

Stop on free-route withdrawal, quota denial, billing ambiguity, unsupported safety
controls, authentication failure, unrecoverable provider/schema failure, budget
exhaustion or expiry. Never switch model/provider automatically. If no verified
free route remains, skip remaining Free-model verification and use mocks for the next mocked verification step.

Rollback: close run kill switch, stop client, disable/delete only the Free-model verification
Preview and remove its scoped credentials. Revoke dedicated backend/visitor
credentials; do not revoke the existing shared OpenRouter key without approval
unless compromised. Environment removal alone does not cleanse immutable builds.
Retain audit records and let existing owned leases/counters expire naturally.
Never promote/redeploy the mock Preview or alter Production during rollback.

Residual risks: free capacity withdrawal, provider data policies, changing weights,
usage reporting lag, provider mishandling of price controls, and shared platform
allowance consumption. The zero-price allowlist/cap and no-tools configuration
are mandatory preventive controls; a post-request cost check alone is insufficient.
Synthetic data only; fra1 does not establish upstream data residency.

Approval requested: implement/review the isolated free-only controls, run focused
offline checks, then create one protected Preview and execute F1–F9 within these
ceilings after fresh free-access checks. No billing, paid inference or fallback
is authorised. Material scope/control changes require another approval.
