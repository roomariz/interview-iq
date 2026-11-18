# Redis lease investigation and local workflow verification

18 November 2026. Local verification complete on `feat/streamlit-vercel-backend`.
No push, deployment, main merge, provider inference or paid provisioning performed.

## Conclusion

**A permanent lease leak has not been established.** The previous hosted observation
was insufficient to classify the lease: it retained only `ZRANGE` member count,
not owner, expiry score, Redis time and key TTL together. Counting members alone
does not measure occupied concurrency capacity.

One authorised read-only inspection at **21:39:11 CET** found the shared lease key
absent (`PTTL=-2`), no members and zero active leases. It used one Redis pipeline
containing TIME, ZRANGE WITHSCORES and PTTL, with **zero hosted application calls**.
No shared state, namespace, lease or counter was changed. This establishes that
the observed member did not persist indefinitely. It cannot establish whether
release, natural key expiry or subsequent admission cleanup removed that member.

No production lease correction is justified by the evidence collected here.
Scoring, model selection, providers, API contracts and security limits are unchanged.

## Lifecycle and ownership

- `Admission` generates an independent 64-hex-character owner per request. Redis
  TIME determines expiry scores; the production lease lifetime is 330,000 ms.
- ADMIT atomically checks quotas, removes scores at or before Redis time, checks
  remaining capacity, debits admitted work and stores the new owned lease.
- RENEW checks that the exact owner exists and its score is still in the future;
  an expired owner cannot renew. The heartbeat runs every 30 seconds.
- RELEASE removes only its supplied owner. Wrong-owner release/renewal cannot
  remove or extend another request's lease; existing real-Redis tests cover both.
- A sorted-set member can expire logically before the shared key's TTL. Another
  lease's acquisition or renewal can keep that key alive. The expired member then
  remains visible to ZCARD until the next admission removes expired scores.
- Effective occupied capacity is the count of scores strictly greater than Redis
  time. A raw ZCARD or key TTL alone cannot classify an individual owner.

## Timeout, cancellation and termination

Normal completion and route exceptions run middleware cleanup and release the
owned lease. A timeout/cancellation sets the shared deadline cancellation event.
If a synchronous provider transport is still running, cleanup deliberately waits
for its transport counter to reach zero before releasing capacity. Returning an
HTTP error does not prove that a synchronous transport has stopped.

Cancellation can occur after Redis commits admission but before the caller receives
its acknowledgement. Local reproduction shows an owned lease with no heartbeat
in this case. It safely expires; assuming immediate release would be incorrect.

Cancellation or process termination can interrupt a finally block or a Redis
release request. An abruptly terminated process cannot complete Python cleanup.
The independent expiry mechanism restores capacity without a DEL/ZREM intervention.
Expiry is bounded from **the last successful acquisition/renewal**, not necessarily
from the start of the HTTP request. A live worker can renew a lease while real
transport work remains; killing that worker stops further renewals.

The previous hosted probes returned 504 at approximately 121 seconds. This task
does not establish why that preceded the configured 150-second aggregate deadline,
nor whether Vercel terminated/froze a particular worker. Those runtime-specific
questions remain for the separately approved hosted observation plan.

## Controlled local Redis results

Disposable Redis ran on loopback port 16391, with persistence disabled. Every new
lifecycle/crash test generated an isolated `lease-local-*` or `lease-crash-local-*`
namespace. No shared managed namespace or unrelated keys were deleted or reset.

| Case | Observed result |
| --- | --- |
| Successful completion | Owned lease removed; next request admitted |
| Backend exceptions | Controlled 502 and unexpected 500; leases removed; next request admitted |
| Aggregate request deadline | Middleware 504 cancels async work and releases its lease |
| Provider timeout | Synthetic 504; capacity retained while synchronous work ran; released after transport exit |
| Request cancellation | Tested after route entry, both async work and active synchronous transport; eventual release and recovery passed |
| Cancellation during admission acknowledgement | Lease remained after Redis commit; no heartbeat; natural expiry restored admission |
| Heartbeat | Actual renewal loop tested with accelerated wait; owner score extended; wrong owner rejected |
| Expired owner | Renewal refused; next ADMIT pruned expired member before capacity check |
| Raw-member false alarm | ZCARD=2 while only one score was active; new request admitted at capacity two |
| Independent processes | Existing real-Redis test: two workers, two admitted and ten busy responses; combined cap enforced |
| Process termination, short test | Killed real worker; another worker recovered after unmodified test lease expired |
| Process termination, production lifetime | Actual 330,000-ms lease; initial TTL 329,985 ms; recovery 330,016 ms after kill, including client overhead; no renewal, clock change or manual mutation |

The full-lifetime process test passed in 335.30 seconds, including startup/teardown.
The 16-ms measurement excess is HTTP/polling overhead, not an extended lease.
Both the normal fast test and the actual production-duration run used the same Lua
and two independent local backend processes. No LLM client was used by those workers.

## Five-question workflow and harness investigation

The prior local UI failure reproduced as `welcome` instead of `question`: imported
local `.env` values had enabled Production controls in the loopback backend, without
the signing key required by those controls. The test now explicitly selects test
environment, memory quotas and no visitor signing key. Production configuration
and authentication are not weakened. Other signed-identity tests remain enabled.

The previous hosted harness interruption was separate: it changed JSON content
while transplanting the old Content-Length header. That client transport failure
was not an application failure. The subsequent accounting assertion also assumed
that attempted work had been admitted. A new regression uses the normal client
serializer for two differently sized payloads, proves correct byte lengths,
preserves the client identity and permits only one explicit retry after 502.

Both normal and simulated-error five-question Streamlit/HTTP runs now pass:

- Five distinct questions, in indices 1Ã¢â‚¬â€œ5; five matching evaluations, in the same order.
- Five generation batches, five validated items each; the current first item is
  displayed and fresh adaptive generation occurs at the next interview step.
- Previous-question context and topic history preserved; one generation per step.
- A controlled backend 502 at question two preserves history, index and identity;
  rerendering does not retry; the explicit retry succeeds without another evaluation.
- No duplicate evaluations on rerender, pending-future polling or error recovery.
- Final summary contains five answers and average scores recomputed from those
  stored evaluations. The three-question case also passes.

The UI test uses synthetic service responses. Packaged permanent-mock tests also
exercise the real evaluation pipeline with synthetic provider output. No live
model quality or hosted Streamlit behaviour is inferred from these local checks.

## Changes and checks

Only test support/regressions and documentation changed in this task:

- `tests/test_local_streamlit_backend.py`: explicit local configuration and summary checks.
- `tests/lease_lifecycle_support.py`: synthetic loopback worker with route-entry marker.
- `tests/test_lease_lifecycle.py`: cancellation, transport lifetime, ownership,
  renewal and expired-member/admission regressions.
- `tests/test_lease_process_recovery.py`: independent-worker termination/expiry test.
- `tests/test_verification_client_recovery.py`: explicit retry/body-length regression.
- User/developer/test manuals and agent constraint history updated; pre-existing
  unrelated working-tree changes preserved. Nothing committed or pushed.

| Check | Result |
| --- | --- |
| Complete automated suite, real local Redis enabled | 762 passed; 11 live/e2e deselected; five existing warnings; 46.50 seconds |
| Added lifecycle cases | Ten cases included in complete suite, including both cancellation paths |
| Actual 330-second process termination run | Passed; measured recovery above |
| Question progression, packaged mock and API contracts | Included in complete passing suite |
| Backend and frontend startup | Both loopback health endpoints returned 200; child servers stopped |
| Backend dependency audit | 26 resolved packages; zero known advisories |
| Frontend dependency audit | 40 resolved packages; zero known advisories |
| Development dependency audit | 82 resolved packages; zero known advisories |
| Installed-environment dependency audit | 96 packages; zero known advisories |
| pip check | No broken requirements |
| Changed-file lint | Passed on all five changed/new Python test files |
| Secret scans | 355 candidate files, staged diff, reachable history and private test receipts: zero configured-value or credential-pattern findings |

Private receipts remain ignored under `.verification-local/lease-*`; source/history
scans compare configured secret values and credential patterns without printing them.
Read-only managed inspection is separate from the completed prior 28-request budget;
no hosted application request was added during this investigation.

## Remaining risks and next approval

Historical owner/expiry evidence was not retained, so a more specific historical
root cause cannot be proved. Local process termination is not a Vercel lifecycle
reproduction. A failed Redis release or killed worker can temporarily retain
capacity until expiry. The hosted five-question UI workflow remains incomplete.

See [the narrow hosted proposal](mock-workflow-recovery-preview-proposal.md).
No replacement backend is required by the test-only changes. Any replacement,
per-deployment namespace override or hosted workflow execution requires separate
approval. Existing protected deployments and their shared configuration are untouched.
