# Protected mocked workflow and lease recovery proposal

Prepared 18 November 2026. **Not executed; separate approval required.**

## Source and deployment boundary

The investigation changed tests and documentation only. No backend correction was
justified; redeployment is not required to deliver those changes. If a replacement
is approved, create exactly one additional protected Preview from the same reviewed
104-file permanent-mock artefact, with no working-tree upload:

- Source: `a222d76b30b83ab280e8537868017769de93e25d`.
- Inventory SHA-256:
  `c9066d3f005c38017ba731860e31d42acb77e894c5af4191db9ecbaf5f7c6364`.
- Personal Hobby owner/project: `roomas-projects/interviewiq-api-preview`.
- Preview only, `fra1`, unchanged Python/runtime/300-second ceiling and limits.
- All Deployments authentication and permanent provider blocking remain mandatory.
- No GitHub push is necessary. No aliases, promotion, Production record or frontend deployment.

Use **one deployment-specific environment override**, never a shared project-variable
edit: `BACKEND_RATE_NAMESPACE=interviewiq-mock-recovery-<random-hex-suffix>`.
The full name must be at most 64 characters, using only letters, digits, `_` and `-`.
Record the actual namespace in the approval/execution receipt before submitting.
Abort if deployment-only overrides cannot be applied without affecting older deployments.

Keep all existing limits and credentials unchanged. Do not copy provider keys or
change model selection. Dummy provider credentials and permanent blocking remain.
Never clear quotas, delete shared state or rotate anonymous identity to evade a cap.

## Minimum work and hard limits

- Five-question UI workflow: 1 context + 5 question generations + 5 evaluations =
  **11 admitted requests**.
- One controlled question-generation 502, followed by the normal explicit retry
  already counted in the five successful generations: **one additional admission**.
- One controlled deadline probe and one subsequent zero-delay context request to
  prove recovered admission: **two further admissions**.
- Proposed hard maximum: **14 admitted requests, 26 verification HTTP attempts**,
  counting client transport failures and Redis diagnostic pipelines in that total.
  No automatic POST retries. No optional sample-answer request or independent
  three-question session. Previously demonstrated auth/schema/load tests are not repeated.
- Control-plane source/protection inspection and upload are recorded separately;
  backend-internal Redis commands are not extra client diagnostic probes.
- Proposed client probes consume 15 application attempts including one unauthenticated
  protection check, leaving at most 11 Redis diagnostic HTTP calls within the cap.

These limits cannot establish capacity-four saturation again. That is covered by
local multi-process tests and is outside this narrow hosted check.

## Execution sequence after approval

1. Read-only preflight: verify owner/Hobby, protection, existing resource metadata,
   source hashes, exact mock isolation and credential absence. Confirm the isolated
   namespace override and that no old deployment/environment record will change.
2. Submit one Preview, verify READY/Preview/`fra1` and all uploaded source hashes.
   Issue one unauthenticated health request and require an authentication denial.
3. Create one synthetic signed identity. Keep a private durable session checkpoint
   before the first request. Never print its token or private header values.
4. Run the ordinary Streamlit/AppTest five-question flow. At question two, add the
   outage marker to the payload **before normal client JSON serialisation**. Do not
   mutate HTTPX requests or transplant Content-Length. Require safe 502; verify the
   existing history, index and identity. Rerender once with no dispatch; explicitly retry.
5. Assert five unique displayed questions, ordered batches and five evaluations,
   exactly one successful generation per step and an accurate five-answer summary.
   Preserve the same identity and naturally wait for its minute window before
   admission 11. Keep attempted and Redis-confirmed admitted counts separate.
6. Take a read-only isolated-namespace baseline using Redis TIME, ZRANGE WITHSCORES,
   PTTL and quota GETs in one pipeline. Record hashed owner IDs, scores and timestamps.
7. Send one deadline probe using the existing permanent mock marker. While pending,
   inspect its own namespace, identify the new owner, and record renewal/expiry.
   A 504 ends the HTTP wait, not necessarily the underlying transport lifetime.
8. Poll read-only snapshots within the remaining 11-pipeline allowance, including
   one after the recorded owner expiry. Classify each owner against Redis TIME;
   do not label raw expired members a leak. The bound is 330 seconds after the
   last successful renewal, allowing client/polling overhead in measurement.
   If renewal continues unexpectedly, stop without extending the request budget.
9. Once the owner is absent or expired, send the single remaining zero-delay
   context request. Require successful admission and subsequent lease release.
10. Inspect sanitised runtime logs privately, compare unchanged old resources and
    produce exact request/admission/latency/failure counts. Stop at the stated caps
    or immediately on protection failure, live-provider traffic, required expenditure,
    critical application failure or a demonstrated security regression.

If an infrastructure request exceeds a cap or an unexpected retry consumes budget,
stop and report the incomplete result. Do not restart or replay completed evaluations.
Protect checkpoints and write the safe ledger before dispatch and after each response,
so a harness exception cannot erase the evidence or reset accounting.

## Rollback and stop

No aliases or shared settings are changed, so rollback does not repoint traffic.
Stop the verification client and leave existing deployments unchanged. If approved
as part of execution, delete **only the newly created replacement Preview** after
capturing its evidence; otherwise leave it protected pending a separate decision.
Never delete Redis keys to accelerate rollback. Owned leases and isolated quotas
expire naturally; retain the namespace in the receipt until then.

No push, deployment, namespace override, hosted application request, live inference
or Streamlit release is authorised by this document. Approval requested is limited
to this single protected mocked replacement and the sequence/limits above.
