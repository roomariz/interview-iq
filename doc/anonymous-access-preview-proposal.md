# Anonymous access controls Preview proposal

Proposal only: no Vercel variable, project, deployment or Production change made.
Owner remains `roomas-projects`, project `interviewiq-api-preview`, Hobby plan.
Keep All Deployments authentication, the existing protected bypass and Frankfurt.
The inert Production bootstrap must remain unchanged.

## Exact proposed variables

Set these on **Preview only** after approval:

| Variable | Proposed value |
| --- | --- |
| BACKEND_VISITOR_SIGNING_KEY | New independent cryptographically random secret, at least 32 bytes; generate privately, do not paste into chat |
| BACKEND_VISITOR_RATE_LIMIT | 10 |
| BACKEND_VISITOR_DAILY_LIMIT | 100 |
| BACKEND_GLOBAL_DAILY_LIMIT | 1000 |
| BACKEND_INGRESS_RATE_LIMIT | 300 |

Keep existing `BACKEND_RATE_LIMIT=30`, `BACKEND_MAX_CONCURRENT=4`,
`BACKEND_REQUEST_DEADLINE=150`, `APP_ENV=production`,
`BACKEND_RATE_BACKEND=redis` and the existing Preview namespace
`interviewiq-mocked-preview`. Preserve the existing API secret, Redis credentials,
provider configuration, model, fallback setting and Preview protection secret.
There are no new provider credentials or external services.

Add the identical visitor signing key to the trusted Streamlit server's private
settings. Do not put it in browser JavaScript, repository files or query strings.
The Streamlit example now shows its name. Deploy/update frontend and backend
together: the new backend rejects older clients that do not send a signed token.
If Streamlit is not yet hosted, the verification client must mint synthetic signed
tokens privately. Keep all provider transports permanently mocked in the artifact.

No Vercel function setting changes are proposed. Preserve Python 3.12, `fra1`,
`maxDuration=300` and disabled automatic Git deployments. The 330-second lease
depends on this execution ceiling. New quota keys use a `v4` prefix/hash tag;
the rollout starts fresh counters and legacy minute counters expire naturally.
Do not run old and new backend revisions as a public mixed-version service.

## Approval-gated verification sequence

1. Review local diff and results; approve any publication and Preview update
   separately. No automatic push/deployment is part of Anonymous access controls.
2. Rebuild the permanent mock overlay from the reviewed revision. Verify all new
   backend/shared modules are packaged; inspect the inventory and network guard.
   Existing Preview artifact hashes describe the earlier revision only.
3. Apply only the proposed Preview variables securely, retain All Deployments
   protection and verify the personal Hobby owner before deploying a new Preview.
4. Verify unauthorised platform/backend requests fail; missing, forged and expired
   visitor tokens fail. No request should contain real CV or provider credentials
   in diagnostic output. Confirm mock transport intercepts every provider call.
5. Give two synthetic visitors independent allowances; verify visitor minute/day,
   global minute/day, concurrency across instances and useful Retry-After values.
   Use a dedicated test namespace/temporarily lowered limits only if separately
   approved; preserve existing Preview secrets and restore approved numeric caps.
6. Check timeout, abandoned transport, lease expiry, Redis outage and invalid Redis
   authentication. Inspect response bodies and platform/runtime logs privately for
   URL/header/body/credential leakage. Restore failure-injection variables.
7. Report results and stop. No Production promotion, public release, live provider
   request or paid resource is authorised by this proposal.
