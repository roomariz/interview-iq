# Phase 5 free-model verification results

18 November 2026. **Stopped at hosted preflight; live verification not completed.**
No inference was performed. No replacement deployment or Phase 6 deployment.

## Execution and limits

| Measure | Result | Approved maximum |
| --- | --- | --- |
| Provider-bearing workflow requests dispatched | **0** | 3 |
| Model attempts, including retries | **0** | 12 |
| Inference input/output tokens | **0 / 0** | 196,608 / 24,576 |
| Paid inference / new cash expenditure | **US$0 / US$0** | US$0 / US$0 |
| OpenRouter free daily usage | **0 used, 50 remaining**, before and after | Existing free allowance |
| Hosted verification requests | 14, all health/auth/schema/context checks | 20 |
| New Vercel Previews | One created, subsequently deleted during rollback | 1 |

The account's pre-existing aggregate usage was unchanged. No credits purchased,
billing enabled, paid model selected, live Google/Ollama/xAI request, Git push,
main merge or Production deployment was performed.

## Free eligibility and prepared controls

- Read-only checks immediately before deployment confirmed the exact
  `google/gemma-4-31b-it:free` route with zero input/output prices and an available
  Google AI Studio endpoint. The existing key reported free-tier status with
  all 50 daily requests remaining. This proves metadata eligibility, not inference.
- The isolated overlay fixed the model ID and provider, set zero maximum prompt,
  completion and request prices, disabled fallbacks, and blocked alternate
  Requests and sync/async HTTPX provider transports.
- Redis Lua enforced three one-use workflow cases and 12 total reservations,
  including nested retries, with one outstanding attempt and per-case limits.
  Every failed/ambiguous send would consume its reservation. The run was never
  opened; its final ledger explicitly records `open=0`, without attempt/workflow
  reservations or provider events.
- Provider responses would require verifiable numeric usage and zero cost before
  another attempt. No model output was received, so those live checks remain untested.

The bounded proposal is [here](phase5-live-provider-proposal.md). Its execution
approval did not authorise a second replacement Preview after this failure.

## Deployment and verification

- Temporary Preview: `dpl_HeJ41M53jPpHMyP7cTWgM7WGBf1K`, personal Hobby
  `roomas-projects/interviewiq-api-preview`, Python 3.12, `fra1`, READY,
  Preview target `null`, no aliases. It has now been deleted.
- Source: commit `69e7d0c8141524446012afea36c017b5c0965ee2` plus isolated
  deployment-only guards. Uploaded source hashes matched all **105 files**.
- Manifest SHA-256:
  `a04e84399437c5ea3f0108e1792bd5da01e9541e99ab606a12d4214be5c813f8`.
- Credentials were deployment-only overrides supplied through process environment
  references, not command-line secret values. No shared Preview variables changed.
- Public/invalid-bypass health requests redirected to Vercel authentication.
  Authorised health returned 200. Backend bearer and signed visitor failures
  returned 401; invalid question count and short answer returned 422.
- The first valid synthetic context request returned a controlled **503 in 61 ms**.
  It did not reach the context service or any provider. No question request followed.

## Preflight defect and stop decision

The new guard compared Redis URLs as literal strings with an appended trailing
slash. Existing quota code constructs its root POST URL without that slash.
HTTPX preserves this distinction in the request URL, so the guard rejected a
legitimate Redis quota request before network dispatch. Existing security then
returned its sanitised 503 rather than admitting work without quotas.

This was an implementation defect in the new overlay, not evidence that the free
model was unavailable. The new guard remained closed and prevented bypass of Redis
controls. Hosted quota/concurrency verification was therefore **not established**
for this artifact, despite its preserved settings and passing offline checks.

No inference was attempted because a mandatory preflight control failed. The
one-Preview allowance was already consumed; no silent redeployment or workaround
was attempted. Further Phase 5 execution needs correction of URL canonicalisation,
a regression test covering the actual Redis request shape, and separate approval
for another isolated deployment. The experimental overlay must not be redeployed
as-is. Normal application startup does not install it.

## Automated verification and secret scans

- **104 affected tests passed** under synthetic settings with external networking
  blocked: free-only guards, SDK wire body, authenticated workflow boundary,
  Redis quotas/admission, identity, deadlines, question and API contracts.
- A real disposable Redis race test admitted exactly one of 32 simultaneous
  attempts competing for the twelfth reservation; no thirteenth was admitted.
- The exact artifact imported successfully with synthetic production-control
  settings. Changed/new Python lint passed. The full mocked suite was not repeated.
- Configured-secret comparison and credential-pattern checks passed across
  **431 source/artifact files**. Uploaded artifact inventory matched exactly.
  Retrieved log output was privately checked against configured secret values.
- Initial broad tests were contaminated by the private development environment;
  rerunning with synthetic settings produced the 104 passing result. No provider
  sockets were available during either test run.

The URL-shape regression was missing from these checks. Passing offline tests
did not supersede the failed hosted preflight.

## Rollback and preserved state

- Closed the run ledger and gave it a 24-hour expiry; no shared quota or lease
  counters were reset or deleted.
- Deleted only the temporary Phase 5 Preview, removing its active deployment
  credentials. The existing shared OpenRouter key was not revoked or changed.
- Rechecked the complete original deployment set: only the three prior deployment
  records remain. Original deployment identities/creation times/aliases, project
  protection/resources and all 20 shared variable records are unchanged.
- Verified mocked Preview `dpl_4ij7fmNGu3hb5ubUHrqrTMwk6wi9` still serves authorised
  health, and inert Production `dpl_3r1dLtGUkZZ38R352icSbajiBTLx` still returns
  protected 503 with its inert header and unchanged body hash.

Local private diagnostics, receipts and failed-artifact inventory remain ignored
under `.phase4a-local/`. No remote temporary Preview remains available to invoke.
Phase 6 was not started: the free route remains eligible, while this stop was due
to a failed deployment safeguard. Phase 6 deployment still requires separate approval.
