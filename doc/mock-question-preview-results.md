# Protected mocked question-progression verification results

18 November 2026. **Stopped: verification is incomplete; no Streamlit release.**

## Deployment and provenance

- [Protected Preview](https://interviewiq-api-preview-5o6y66fvf-roomas-projects.vercel.app)
- Identifier: `dpl_4JAXi8eLeqeDEUpu6FoFRiNYh1so`; READY, Preview (`target=null`), `fra1`, Python 3.12.
- Personal Hobby owner: `roomas-projects`; project `interviewiq-api-preview`.
- Approved source: `roomariz/interview-iq`, `feat/streamlit-vercel-backend`,
  `a222d76b30b83ab280e8537868017769de93e25d`.
- Pushed only that commit from previous feature tip `cef29b8`.
- Remote main remains `164fe226c95af6259d5f67170e1e20965d4c280b`.
- Exactly 104 uploaded source files match the reviewed inventory, using Vercel's
  source content identifiers against local SHA-1 and the approved local SHA-256
  inventory. Vercel's generated `out/fastapi` function is separate build output.
- Artefact inventory SHA-256:
  `c9066d3f005c38017ba731860e31d42acb77e894c5af4191db9ecbaf5f7c6364`.
- Windows overlay line-ending transformations were reproduced byte for byte;
  no artefact code or reviewed hash was changed.
- No unrelated working-tree changes were uploaded or pushed. Vercel's automatic
  `gitDirty=1` metadata reflects the existing dirty repository, not extra uploads.

## Stop reason and limitations

The final read at **21:34:05 CET** showed **one remaining Redis work lease** after
both concurrent probes had returned 504. Earlier assertions expecting an empty
lease set failed. Automatic lease release is therefore **not verified**; there
were no further remote actions after the final read. No lease or quota was
cleared, shortened or changed. Whether the lease later expired is unverified.
This is an unresolved security-control gate, not a successful concurrency pass.

The first UI harness also failed its own accounting assertion after question four.
Its injected question-two request encountered a client transport error caused by
rebuilding the request with an outdated Content-Length. Redis confirmed that
attempt consumed **zero** admissions. An explicit retry retained the running UI's
history, question index and anonymous identity and did not repeat an evaluation.
This demonstrates transport-error recovery, not hosted provider-error recovery.

The three-question summary was reached using the first three hosted pairs, as
approved by the user. Four pairs completed in that original UI session. A fifth
pair subsequently passed through the hosted API in a supplemental client with a
new synthetic identity and reconstructed synthetic previous-question context.
It did not resume the interrupted UI. **A complete five-question UI workflow,
five-question summary and independent three-/five-question sessions are unverified.**
No completed evaluation was replayed. The separate controlled provider-outage
request returned a sanitised 502; UI recovery from that 502 was not exercised.

## Results

| Check | Result |
| --- | --- |
| Permanent mocked artefact | Exact-source local check passed five unique questions, five evaluations and an example answer |
| Provider isolation | Requests plus synchronous/asynchronous HTTPX blocked all four provider paths; Production, live keys and enabled fallback refused locally |
| Credentials | Configured-value/pattern scan of source, staged diff and reachable history found none; exact artefact scan passed |
| Platform authentication | Missing and invalid bypass returned 302; valid header reached health with 200 |
| Backend/visitor authentication | Missing bearer, missing visitor and forged visitor each returned 401 |
| Invalid schema | Returned 422 before admitted work |
| UI question batches | Four adaptive generation requests each returned five questions; UI selected the first validated item and regenerated at the next step |
| Adaptive context | Question indices 1–4 carried previous-question counts 0, 1, 2, 3; rerenders dispatched no extra generation/evaluation |
| Question uniqueness | Original UI's four displayed questions were distinct; supplemental fifth API question passed validation |
| Evaluation | Five successful hosted evaluations overall: four original UI, one supplemental API; follow-up present on supplemental response |
| Summaries | Three-question UI summary reached; five-question summary unverified |
| Error recovery | Client transport failure recovered through explicit retry without changing UI history, index or identity; no automatic retry on rerender |
| Synthetic provider outage | Separate example-answer request returned safe 502; raw outage message absent |
| Redis quota accounting | Global daily count moved from 13 to 27: exactly 14 admissions, including controlled failures |
| Quota configuration | Visitor 10/minute and 100/day; global 30/minute and 1,000/day; ingress 300/minute; concurrency four; all preserved |
| Quota denial/reset | Not freshly verified; harness stopped before the intended minute-denial check; no counters/reset/namespace changes |
| Concurrent admission | Two simultaneous hosted requests had two distinct shared Redis leases |
| Deadline response | Two controlled 504s at 121.125s and 121.141s; this does not establish the full 150s aggregate deadline behaviour |
| Lease release | Failed verification: one lease remained at final read; capacity-four denial, cross-instance saturation and expiry not re-exercised |
| Logging | 84 retrieved build/runtime records were scanned privately: no configured credentials, Redis endpoint/hostname, synthetic answer text or outage/deadline markers |
| Log coverage | Retrieved runtime window ended before final timeout outcomes; late timeout/cleanup logs were not retrieved after the stop |
| Approved-source local progression/recovery/UI checks | 19 passed in isolated approved source |
| Root focused package/progression/UI run | 22 passed, three UI tests failed against dirty working-tree frontend; these changes were excluded from deployment |
| Local admission/identity/logging checks | 27 passed; external networking blocked by tests |
| Existing resources | Metadata comparison passed for old mock and inert bootstrap; all 20 Preview-only variable records, protection and resource settings unchanged |
| Deployment count | Exactly one additional Preview; no new Production record |

The Vercel connector denied access to the personal scope. Existing explicitly
scoped CLI authentication succeeded; no connector permissions were changed.
No live provider calls, paid inference, new paid infrastructure, variable changes,
Production deployment, main merge, alias promotion or Streamlit deployment occurred.

The existing verified mock remains `dpl_4ij7fmNGu3hb5ubUHrqrTMwk6wi9`; inert
Production bootstrap remains `dpl_3r1dLtGUkZZ38R352icSbajiBTLx`. Their target,
creation time, URL, aliases and READY status match the preflight. The planned
postflight bootstrap HTTP probe was not executed because verification stopped.

## Exact request accounting

- **22 application HTTP attempts**: 21 completed responses and one client transport
  failure; the failed attempt is conservatively included in the budget.
- **Six read-only Redis diagnostic HTTP requests**, each using a pipeline.
- **28 total verification data-plane attempts**, below 30 even including Redis.
- **14 admitted work requests**, confirmed by global Redis debit, below 15.
- Application status totals: 12 × 200, 2 × 302, 3 × 401, 1 × 422, 1 × 502,
  2 × 504, 1 transport failure. Expected deliberate failures are included.
- Successful application responses: minimum 0.109s,
  median 0.141s, maximum 0.375s.
- Vercel/GitHub control-plane inspection, source upload and branch publication are
  separate from these application/Redis verification requests. Backend-internal
  Redis commands are not additional client probes and were not individually counted.
- Raw private receipts and safe request ledger remain ignored under
  `.verification-local/`; credentials are absent from this report and ledger.

| # | Kind | Request | Result | Seconds |
| --- | --- | --- | --- | --- |
| 1 | application | GET /api/health | 302 | 0.297 |
| 2 | application | GET /api/health | 302 | 0.203 |
| 3 | application | GET /api/health | 200 | 0.344 |
| 4 | application | POST /api/interview/context | 401 | 0.188 |
| 5 | application | POST /api/interview/context | 401 | 0.047 |
| 6 | application | POST /api/interview/context | 401 | 0.063 |
| 7 | application | POST /api/interview/question | 422 | 0.078 |
| 8 | redis-read | POST /pipeline | 200 | 0.078 |
| 9 | application | POST /api/interview/context | 200 | 0.156 |
| 10 | application | POST /api/interview/question | 200 | 0.156 |
| 11 | application | POST /api/interview/evaluate | 200 | 0.14 |
| 12 | application | POST /api/interview/question | transport_failure | 0.047 |
| 13 | application | POST /api/interview/question | 200 | 0.14 |
| 14 | application | POST /api/interview/evaluate | 200 | 0.14 |
| 15 | application | POST /api/interview/question | 200 | 0.141 |
| 16 | application | POST /api/interview/evaluate | 200 | 0.375 |
| 17 | application | POST /api/interview/question | 200 | 0.141 |
| 18 | application | POST /api/interview/evaluate | 200 | 0.125 |
| 19 | redis-read | POST /pipeline | 200 | 0.078 |
| 20 | application | POST /api/interview/example-answer | 502 | 1.266 |
| 21 | application | POST /api/interview/question | 200 | 0.109 |
| 22 | application | POST /api/interview/evaluate | 200 | 0.109 |
| 23 | application | POST /api/interview/example-answer | 504 | 121.125 |
| 24 | application | POST /api/interview/example-answer | 504 | 121.141 |
| 25 | redis-read | POST /pipeline | 200 | 0.016 |
| 26 | redis-read | POST /pipeline | 200 | 0.078 |
| 27 | redis-read | POST /pipeline | 200 | 0.109 |
| 28 | redis-read | POST /pipeline | 200 | 0.079 |

No further hosted verification, remediation, replacement, inference or Streamlit
release was performed. Lease investigation and completion of the five-question UI
workflow require a separate scoped task/approval; this report does not approve them.
