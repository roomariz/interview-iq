# Free-model verification execution results

18 November 2026. **Hosted preflight passed; live verification stopped on HTTP 429.**
No answer evaluation or third workflow was attempted. No next-stage deployment.

## Preview and source

- Preview URL:
  [interviewiq-api-preview-5s3zjgygk-roomas-projects.vercel.app](https://interviewiq-api-preview-5s3zjgygk-roomas-projects.vercel.app).
  **Rolled back and deleted after the rate-limit failure; this is a historical URL.**
- Deployment ID: `dpl_Pt1uYr6dhz3ZT4GEa42oCzt99mqP`.
- Personal Hobby owner/project: `roomas-projects/interviewiq-api-preview`.
- Repository: `roomariz/interview-iq`; branch `feat/streamlit-vercel-backend`.
- Approved/published commit: `cef29b880de0e003aa83567eb9fd5a0c368e5bf6`.
- Only that commit was pushed. Remote `main` was checked unchanged; no merge.
  Subsequent staged descriptive renames and other local edits were not published.
- Exactly one replacement Preview was created: Python 3.12, `fra1`, target `null`,
  READY, no aliases. No Production deployment or shared environment changes.
- All **106 uploaded source hashes** matched the reviewed artifact derived from
  the approved commit. Manifest SHA-256:
  `89cb4d74e93e9f88cfc60fd442bf7e9fda374b4290e05cd4b2764c90da77f654`.

The deployed artifact retained the approved commit's internal module/configuration
names. Renamed working-tree files were deliberately excluded from the exact-source
publication and deployment boundary. This report uses descriptive workflow names.

## Checks before inference

| Check | Evidence/result |
| --- | --- |
| Exact-source focused tests | 75 passed, including free-only SDK wire controls, Redis URL equivalence, workflow limits and final-attempt concurrency race; provider networking blocked |
| Previous complete automated suite | 711 passed; no full-suite repetition during execution |
| Secret scans | 434 isolated source/artifact files and reachable approved history passed configured-secret and credential-pattern scans |
| Build/runtime privacy | Retrieved output excluded configured secrets and synthetic interview inputs |
| Free route | Exact `google/gemma-4-31b-it:free` endpoint available with zero prompt/completion pricing before deployment and again at the outbound attempt |
| Account eligibility | Authenticated metadata returned free-tier status and 50 free requests remaining; quota rechecked immediately before opening the run |
| Single-model/provider boundary | Exact model only; Google AI Studio endpoint only; zero prompt/completion/request price caps; provider fallbacks disabled; other provider credentials empty |
| Budgets | Redis atomic ledger: three one-use workflows, 12 total attempts including retries, one outstanding attempt and 30-minute expiry |
| Deployment protection | Public/invalid-bypass health redirected to Vercel authentication; authorised health passed |
| Backend/visitor authentication | Missing/invalid bearer and missing/forged visitor tokens returned 401 |
| Input schema | Wrong question count and short answer returned 422 without model requests |
| Redis correction | Valid hosted context returned 200, debited managed quotas and released its owned lease |
| Quotas/concurrency | Existing visitor 10/minute and 100/day; global 30/minute and 1,000/day; four distributed leases and ingress 300/minute preserved. Admission source hashes unchanged; local race checks passed |
| Existing deployments/secrets | Original identities, protection/resources and all 20 shared variable records matched the verified baseline |

No hosted quota-exhaustion/load test was repeated. This execution confirms normal
managed quota admission and lease release; it is not a new concurrency load benchmark.

## Actual workflow results and usage

| Item | Actual result | Approved ceiling |
| --- | --- | --- |
| Live workflow requests dispatched | **1**: synthetic question generation | 3 |
| Outbound provider attempts | **1**, exact selected free model | 12, including retries |
| Additional outbound retries | **0**; closed guard blocked further sends | Within the same 12 |
| Successful model completions | **0** | No completion target overrides the stop conditions |
| Question endpoint wall latency | **12,640 ms** | Existing 150s deadline |
| Reserved attempt wall latency | **244 ms**, including its price check and rejected provider request | Existing 60s provider timeout |
| Provider result | **HTTP 429** | Stop immediately on unavailable/rate-limited free route |
| Application response | HTTP 200 containing a local safe fallback; live metadata empty | Fallback must never count as a live-model pass |
| Structured model JSON | Not available; provider rejected the request | Application/provider schema validation remains required |
| Answer evaluation | Skipped | Only after successful live question generation |
| Third workflow/follow-up | Skipped | Only after successful evaluation |
| Inference token usage | Not returned for the rejected request; no accepted completion | Input/output reservations below |
| Reserved input/output allowance | 16,384 / 2,048 tokens, conservatively retained for the one attempt | 196,608 / 24,576 total |
| Paid inference/account charge delta | **US$0** observed | US$0 |
| New cash expenditure | **US$0** | US$0 |
| Free daily counter before/after | **0 used, 50 remaining** in both authenticated snapshots | Existing account allowance |
| Hosted verification HTTP requests | **15**, including preflight and question request | 20 |

The provider returned 429 even though the published endpoint was available and
the account reported unused daily quota. This establishes a rate/capacity denial;
the retained numeric telemetry does not identify whether OpenRouter or its
upstream endpoint imposed it. No retry, paid route, model substitution, billing
activation or credit purchase was attempted.

The guard closed the run on the first provider error. Application-side failure
handling still returned a safe fallback question, which the verifier correctly
rejected as a live success. Internal error/fallback processing accounts for the
endpoint taking longer than the single outbound attempt; no additional outbound
provider call was made.

Token counts for a rejected request were not supplied, so they are reported as
unknown rather than invented zeroes. The account's reported charged usage was
unchanged, its daily charged usage remained zero and the free-request counter was
unchanged at the final check. Provider accounting can lag; the single attempted
request remains charged against our local attempt budget regardless of that counter.

## Stop, rollback and preserved state

- Recorded `open=0`, one workflow and one provider attempt in the run ledger.
  There was no outstanding attempt at close. No shared quota/lease keys were reset.
- Deleted only the temporary replacement Preview under the proposed rollback
  procedure, removing its active deployment credential copy. No new Preview retry.
- The existing shared OpenRouter key was not revoked or modified. Temporary local
  credential copies are removed after audit capture; receipts remain ignored under
  `.verification-local/approved-replacement/`.
- Final cloud metadata matched the original three-deployment set. Mocked Preview
  `dpl_4ij7fmNGu3hb5ubUHrqrTMwk6wi9` and inert Production bootstrap
  `dpl_3r1dLtGUkZZ38R352icSbajiBTLx` remained unchanged, as did protection,
  resources, aliases and all 20 shared variable records.
- Protected bootstrap health/body hash was checked during preflight. No Production
  promotion, domain assignment, paid service or main-branch merge occurred.

## Remaining risks and recommendations

1. Live model quality, structured-output reliability, scoring and follow-up
   generation remain unverified. Metadata availability and free quota do not
   guarantee serving capacity. Do not describe this run as a successful live test.
2. Keep the next verification step mocked: exercise the complete interview flow
   and frontend/API boundary using the existing permanent mock response path.
   Confirm that scope before implementation; deployment requires separate approval.
3. For a separately approved future live attempt, retain the same zero-spend and
   single-model boundaries. Check rate-limit reset information before scheduling
   a new bounded run; never replace free capacity with paid inference automatically.
4. Consider retaining sanitised 429 classification, Retry-After and provider request
   identifiers in future telemetry. The present guard safely stopped, but did not
   retain enough upstream diagnostics to attribute this particular denial.

Verification has stopped. No next-stage implementation or deployment is authorised
by this report.
