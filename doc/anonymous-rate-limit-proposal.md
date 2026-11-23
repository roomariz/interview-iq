# Anonymous quota design proposal — assessment only

Current controls share 30 authenticated HTTP requests per 60-second Redis window
across every visitor using the Streamlit backend credential. Context and failed
validation requests count too. A visitor can exhaust everyone else's access.
The per-process concurrency counter of four multiplies as Vercel scales.
These controls are acceptable for a protected synthetic Preview, but insufficient
for fair public access or a hard inference budget. No identity/quota change is implemented.

## Proposed design requiring separate approval

1. Issue an opaque, unpredictable anonymous visitor identifier through a trusted
   same-origin bootstrap. Persist a signed Secure, HttpOnly, SameSite cookie with
   an explicit expiry; have the Streamlit server forward a validated signed token
   to the backend. This needs deliberate integration with Streamlit's session and
   origin model. Do not trust arbitrary browser IDs, X-User-ID or forwarded IP headers.
2. Enforce per-visitor short-window and daily allowances in Redis, alongside a
   shared application minute/day budget. Derive identifiers with server-side HMAC
   and keep personal/CV/answer data out of quota keys. The existing backend bearer
   still authenticates the frontend server; the visitor token serves a separate purpose.
3. Use one Lua admission operation to inspect both applicable quotas and acquire
   a distributed concurrency lease before committing admitted usage. Denied or
   busy requests should not debit expensive-work allowances; keep a separate
   inexpensive ingress/invalid-input throttle. Use Redis time, atomic expiry and
   sanitised 429/Retry-After or 503 responses. Redis failure remains fail-closed.
4. Set a shared cap of four active application work leases across all processes.
   Give each lease a random ownership token and expiry exceeding the 150-second
   request budget plus cleanup grace (for example 165 seconds). Release only the
   owned lease in finally. A crashed/expired worker must not free another request's
   slot. Bound or terminate underlying work before its lease expires; HTTP timeout
   alone does not prove synchronous work stopped. Account for each inference fan-out.
5. Cookie deletion/browser resets cannot be prevented for anonymous users.
   Rate-limit new identifier issuance using trusted-ingress signals, short-lived
   HMAC IP-prefix buckets and challenges after repeated issuance. Allow for shared
   networks; IP is a secondary abuse signal, not a visitor's identity. Set explicit
   privacy/retention rules and avoid device fingerprinting. A signed cookie stops
   forgery, not repeated legitimate re-issuance or VPN/distributed abuse.
6. Always retain global minute/day and distributed concurrency limits, even when
   a new visitor token is issued. Add provider-side spending controls where
   supported; keep fallback disabled unless separately approved. Bound input/output
   sizes, token budgets and retries; several provider operations can occur per API
   request, so a request allowance is not a model-call or spending allowance.

Keep the global 30/minute and proposed distributed four as conservative initial
caps. Choose visitor/day and application/day budgets only after an approved cost
and traffic model; no defensible public numeric allowance follows from mock tests.
Use lower-cost context/invalid-input quotas separately so they cannot trivially
consume an inference allowance. Monitor counts/status/latency without prompts or
credentials. Validate atomic admission, lease expiry/ownership, resets, multiple
processes, shared networks and outage behaviour before public access.

For the first release, a protected/invite-limited pilot is simpler to operate while
these controls and actual model latency/cost are measured. A public anonymous
service cannot promise one quota per person without stronger identity checks.
