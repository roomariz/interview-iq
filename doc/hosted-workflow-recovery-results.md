# Protected mocked workflow recovery verification results

Completed 18 November 2026. **Five-question workflow passed; verification stopped.**
All provider output was synthetic. No Streamlit deployment or live inference.

## Publication and deployment

- [Protected Preview](https://interviewiq-api-preview-28ndht991-roomas-projects.vercel.app)
- Deployment: `dpl_3XLLkftWMZQx7U8bJwjXJG6NraRt`; READY; Preview (`target=null`); `fra1`; Python 3.12.
- Personal Hobby owner/project: `roomas-projects/interviewiq-api-preview`.
- Reviewed verification commit: `e247aba79a9166e26cb30c9287287d9563d4e83c` on
  `roomariz/interview-iq`, `feat/streamlit-vercel-backend`.
- Exactly 11 approved test/documentation files committed and pushed. The test support
  was made independent of unrelated pending file renames; no runtime correction
  was justified or included. Unrelated staged/working-tree changes were preserved.
- Main remains `164fe226c95af6259d5f67170e1e20965d4c280b`; no merge or push to main.
- Backend source bytes remain those of `a222d76b30b83ab280e8537868017769de93e25d`.
- Exact reviewed permanent mock: **104 files**, uploaded source content identifiers
  all matched. Inventory SHA-256:
  `c9066d3f005c38017ba731860e31d42acb77e894c5af4191db9ecbaf5f7c6364`.
- No frontend, tests, private settings, credentials or unrelated working files uploaded.
- Isolated deployment-only override:
  `BACKEND_RATE_NAMESPACE=interviewiq-mock-recovery-a2cd39dbe4e80ecc`.
  The existing 20 shared Preview-only variable records were unchanged. First-request
  quota observations confirmed that the new deployment used this isolated namespace.

All Deployments authentication was checked before submission and afterward. Exactly
one new Preview was created. The existing protected Preview deployments and inert
Production bootstrap metadata, resource settings and Hobby plan were unchanged.
Only the original inert bootstrap remains a Production record; no alias promotion.
Connector access to this owner remained unavailable; existing explicitly scoped CLI
credentials were used without changing connector permissions or credentials.

## Five-question workflow

The real Streamlit/AppTest frontend ran locally against this protected hosted backend.
The same anonymous identity and UI session survived the entire run, including the
quota wait, synthetic error and long lease observation. Private durable checkpoints
and request/response receipts were written before/after work, without public tokens.

| Requirement | Result |
| --- | --- |
| Five distinct questions | Passed, indices 1–5, no repeated displayed question |
| Batch ordering/consumption | Five-item validated batches ordered 1–5; UI displayed the current first item and generated a new adaptive batch at the next step |
| Adaptive progression | Previous-question counts 0, 1, 2, 3, 3; topic/adaptation history retained; five adaptation events |
| Five evaluations | Exactly five successful evaluation HTTP requests; no duplicated evaluation on rerender, polling or retry |
| Controlled backend error | Question two returned sanitised 502 `provider_failure`; history, question index and anonymous identity retained |
| Explicit recovery | No retry on rerender; one explicit retry of question two succeeded; no extra evaluation |
| Accurate summary | Five stored answers, corresponding questions in order, five-question summary and recomputed average scores matched |
| Capacity recovery | Interview paused after question four; fifth generation succeeded after the recorded timeout lease became inactive, then fifth evaluation and summary completed |

The synthetic outage marker was applied to a request role field before normal JSON
serialisation. It was removed on explicit retry; the UI role/state did not change.
Local rehearsal caught that the generic focus field did not reach the mock prompt,
and confirmed the corrected injection before any hosted test request was sent.

## Hosted quotas, authentication and deadlines

- Unauthenticated health redirected to Vercel authentication; authenticated requests
  used header-only bypass, backend bearer and the same signed visitor token.
- Fresh backend bearer denial: **True.
- After exactly ten admissions the same visitor received 429 with Retry-After.
  Redis counts stayed at ten. The existing minute window expired naturally; no
  identity rotation, counter reset, lowered cap or namespace change occurred.
- Final admitted visitor/day and isolated global/day counters: **13 each**.
- Remaining visitor minute/day: **8 / 87**; global minute/day:
  **28 / 987**, as of the final Redis snapshot. Minute counts expire
  naturally, so these are time-specific allowances, not permanent reservations.
- Visitor 10/minute and 100/day, global 30/minute and 1,000/day, ingress 300/minute,
  distributed capacity four, 150-second aggregate deadline and 330-second lease
  lifetime remained unchanged. Daily exhaustion and capacity-four saturation were
  not repeated within this bounded check; local multi-process regressions passed.
- Deadline probe returned sanitised 504 `timeout` at **121.172 seconds**. This is
  consistent with the unchanged two 60-second transport attempts and one-second
  backoff inside the 150-second aggregate deadline; it was an application error
  response, not evidence that the aggregate deadline or function ceiling was reached.

## Lease ownership, renewal and recovery

Only `interviewiq-mock-recovery-a2cd39dbe4e80ecc` was inspected. No shared or unrelated lease data was
queried, deleted, rewritten or reset during this verification. Sanitised owner hash:
`efb60dd1b38becb8a3ee6c6314ed5a3962995d559f2d5f6db0d36fb64200791e`. Raw owner identifiers, visitor identities and credentials are withheld.

The same owned lease's expiry advanced under heartbeat renewal. After the HTTP 504
it remained active with 328,753 ms key TTL. The client then made no further application
request until the recorded owner expiry observation. The owner was subsequently
**owner absent** with zero active leases. The fifth question
proved admission recovery; final snapshots showed no leases after normal completion.

This proves recovery by the recorded expiry observation without manual intervention.
It does **not** distinguish key expiration from a delayed release that happened
between snapshots, nor establish Vercel's exact post-response cleanup scheduling.
Immediate release at HTTP timeout was not observed. No permanent leak was established.

| Snapshot | Redis time (CET) | Raw members | Active scores | Observed owner expiry (epoch ms) | Key TTL ms |
| --- | --- | --- | --- | --- | --- |
| 1 | 22:03:50.562 | 0 | 0 | Absent | -2 |
| 2 | 22:03:52.821 | 0 | 0 | Absent | -2 |
| 3 | 22:04:00.514 | 0 | 0 | Absent | -2 |
| 4 | 22:04:54.313 | 1 | 1 | 1795036222212 | 327898 |
| 5 | 22:05:27.595 | 1 | 1 | 1795036252233 | 324638 |
| 6 | 22:06:53.544 | 1 | 1 | 1795036342297 | 328753 |
| 7 | 22:12:22.932 | 0 | 0 | Absent | -2 |
| 8 | 22:12:25.871 | 0 | 0 | Absent | -2 |
| 9 | 22:12:52.687 | 0 | 0 | Absent | -2 |

## Exact accounting and timings

- **25 total verification HTTP attempts**, including all Redis diagnostic pipelines.
- **16 application attempts**, **9 read-only Redis diagnostic attempts**.
- **13 admitted requests**; zero uncertain/pending admissions or transport failures.
- Approved caps: 26 attempts / 14 admissions. Unused budget: **1 attempts / one admission**.
- Application statuses: `{'302': 1, '200': 11, '502': 1, '429': 1, '504': 1, '401': 1}`.
- Successful application response times: min **0.125s**, median
  **0.297s**, max **1.781s**.
- Expected failures were the controlled 502, quota 429, timeout 504 and authentication
  denials. No unexpected application failure or mandatory stop condition occurred.
- Vercel/GitHub control-plane inspection, upload and feature publication are separate
  from verification data-plane attempts. Backend-internal Redis commands are not
  additional client diagnostic probes. No automatic HTTP POST retry was used.

| # | Kind | Request | Status | Seconds |
| --- | --- | --- | --- | --- |
| 1 | application | GET /api/health | 302 | 0.313 |
| 2 | redis-diagnostic | POST /pipeline | 200 | 0.109 |
| 3 | application | POST /api/interview/context | 200 | 0.469 |
| 4 | application | POST /api/interview/question | 200 | 0.187 |
| 5 | redis-diagnostic | POST /pipeline | 200 | 0.063 |
| 6 | application | POST /api/interview/evaluate | 200 | 0.343 |
| 7 | application | POST /api/interview/question | 502 | 3.188 |
| 8 | application | POST /api/interview/question | 200 | 0.297 |
| 9 | application | POST /api/interview/evaluate | 200 | 0.125 |
| 10 | application | POST /api/interview/question | 200 | 0.172 |
| 11 | application | POST /api/interview/evaluate | 200 | 0.438 |
| 12 | application | POST /api/interview/question | 200 | 0.156 |
| 13 | application | POST /api/interview/evaluate | 200 | 0.125 |
| 14 | application | POST /api/interview/context | 429 | 0.125 |
| 15 | redis-diagnostic | POST /pipeline | 200 | 0.047 |
| 16 | application | POST /api/interview/example-answer | 504 | 121.172 |
| 17 | redis-diagnostic | POST /pipeline | 200 | 0.062 |
| 18 | redis-diagnostic | POST /pipeline | 200 | 0.078 |
| 19 | redis-diagnostic | POST /pipeline | 200 | 0.109 |
| 20 | redis-diagnostic | POST /pipeline | 200 | 0.094 |
| 21 | application | POST /api/interview/question | 200 | 1.781 |
| 22 | application | POST /api/interview/evaluate | 200 | 0.36 |
| 23 | redis-diagnostic | POST /pipeline | 200 | 0.063 |
| 24 | application | POST /api/interview/context | 401 | 0.125 |
| 25 | redis-diagnostic | POST /pipeline | 200 | 0.062 |

## Local and security evidence

- Original working-tree verification: 762 passed; 11 live/e2e excluded; five warnings.
- Exact isolated publication source: 742 passed, five opt-in tests initially skipped;
  all five then passed with their original Redis opt-in variable enabled. Eleven
  live/e2e cases stayed excluded. Independent exact-artifact isolation checks passed.
- Verified client rehearsal: complete five-question flow, safe 502 and summary,
  12 synthetic admissions against loopback permanent mock before hosted execution.
- Actual 330-second killed-worker expiry test from preparation: recovery at 330.016s,
  no manual Redis mutation. Startup checks and changed-file lint passed.
- Backend/frontend/development/installed dependency audits: 26/40/82/96 packages,
  zero known advisories; dependency manifests unchanged; pip check passed.
- Proposed source tree, diff, reachable history and exact artefact scanned against
  configured secret values and credential patterns; no populated credentials included.
- Final private log scan: **99 records**, no configured credentials,
  signed visitor token, Redis endpoint/hostname, synthetic answer text or raw outage
  marker. Python 3.12 confirmed. No omitted log page reported.

## Remaining limitations and stop

This was synthetic protected backend verification through a local frontend harness.
No live model quality, public abuse resistance or hosted Streamlit installation was
validated. Capacity-four saturation, the complete daily caps and ambiguous acquisition
cancellation were covered locally/previously, not newly stressed in this hosted run.

The earlier historical lease could not be individually correlated because its owner
and score were not retained. This run corrects that observation gap and demonstrates
bounded recovery, while leaving immediate post-timeout release unproved.

No old deployment or shared configuration was modified, and no paid service or plan
upgrade was provisioned. No paid inference, cash/credit purchase or live provider call.
The replacement remains protected. No further hosted request, deployment, promotion
or Streamlit release is authorised by this result; stop pending separate approval.
Private evidence remains ignored under `.verification-local/workflow-recovery-*`.
