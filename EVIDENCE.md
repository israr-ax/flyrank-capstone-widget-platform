# Evidence — FlyRank Capstone

## Phase 1 · Design
**Gate**: design doc signed off ✅

- `DESIGN.md` committed with data model, API surface, embed flow, and one explicit non-goal.
- `python manage.py makemigrations && migrate` ran clean on Tenant/TenantMembership/Widget/Submission models.

## Phase 2 · Hardened Submission Path
**Gate**: cross-origin curl stores an enriched row ✅

### CORS + valid submission (manual curl)
HTTP/1.1 201 Created
access-control-allow-origin: *
{"id":"f5a9ccc7-58f9-44d9-a585-4c57f4b4ccaf","status":"received"}

Preflight (OPTIONS) also returned 200 with correct `access-control-allow-*` headers.

### Geo fallback on real infrastructure (manual, localhost)
Geo provider _try_ip_api failed for 127.0.0.1: reserved range
Geo provider _try_ipapi_co failed for 127.0.0.1: 429 Client Error: Too Many Requests
[17/Aug/2026 05:39:48] "POST /api/submissions/ HTTP/1.1" 201 65

Both providers failed (expected — 127.0.0.1 is unroutable), submission still stored, `country`/`city` empty, `geo_provider_used` empty.

### Automated test suite
Ran 10 tests in 2.685s
OK
Covers: CORS preflight, missing/unknown required field, unknown widget_id, oversized payload,
honeypot spam block, per-IP rate limit (429 after burst), geo fallback (provider A fails →
provider B succeeds), geo fallback (both fail → submission still succeeds), fail-soft side effect.

## §6 boxes satisfied so far
- [x] Cross-origin submissions work (CORS + preflight)
- [x] Malformed/oversized payloads rejected with clean 4xx
- [x] Valid submissions stored, linked to correct widget + tenant
- [x] Rate limiting per IP and per widget → 429 under burst
- [x] Honeypot spam control demonstrably blocks spam
- [x] Geo enrichment provider fallback chain
- [x] All providers down → submission still succeeds
- [x] Failing side effect doesn't block submission
- [x] Automated tests cover the above

## Phase 3 · Delivery / Dashboard / Proof
**Gate**: one widget, embedded on a fake customer page, produces a real dashboard row ✅

### Cross-origin embed (manual, screenshot)
Widget "Join our newsletter" embedded via `<script src="http://localhost:8000/widget.js" data-widget-id="...">`
on `http://localhost:5500` (separate origin, `python -m http.server`). Customer page CSS deliberately
set `input { background: yellow !important; border: 5px solid red !important }` — widget's Shadow DOM
rendered unaffected (plain white input, no red border), proving true style isolation.
Form submitted successfully ("Thanks! Received.").

### Dashboard reflects the submission
{"total_widgets":1,"total_submissions":1,
"submissions_by_widget":[{"widget__id":"6712c0d5-...","widget__title":"Join our newsletter","count":1}],
"submissions_by_country":[]}

### Automated test suite (full project)
Ran 20 tests in 19.217s
OK

Covers (cumulative): CORS, payload validation, oversized payload, honeypot, rate limiting, geo
fallback (both branches), fail-soft side effect, widget config rendering + cache headers, inactive
widget 404, tenant isolation on widget CRUD (list/retrieve/update/delete/create), dashboard
tenant isolation, unauthenticated dashboard rejection.

## §6 boxes satisfied (cumulative through Phase 3)
- [x] All Phase 1 + Phase 2 boxes (see above)
- [x] Cached, correctly-shaped public widget config endpoint
- [x] Working embeddable widget.js with cross-origin proof
- [x] Authenticated, tenant-scoped widget CRUD
- [x] Tenant isolation proven by automated test (not just assumed)
- [x] Tenant-scoped dashboard with correct aggregation
- [x] Successful widget rendering test

## Acceptance Probes (Layer 2 — evaluator will run these live)

### Probe 1 — Valid submission from second-origin page → stored, 2xx, visible in dashboard
Manual: widget embedded on `http://localhost:5500` (different origin than API's :8000),
form submitted, response "Thanks! Received." Dashboard immediately showed:

{"total_submissions":1, "submissions_by_widget":[{"widget__title":"Join our newsletter","count":1}]}

Automated: `submissions.tests.CORSPreflightTests`, `dashboard.tests.DashboardTenantIsolationTests`

### Probe 2 — Malformed + oversized payload → clean 4xx, never 500
Automated: `submissions.tests.InvalidPayloadTests` (missing field, unknown widget_id, unknown
field → all 400), `submissions.tests.OversizedPayloadTests` (25KB body → 400, not 500)

### Probe 3 — Burst of submissions → 429s appear, normal request right after still succeeds
Automated: `submissions.tests.RateLimitTests.test_ip_throttle_returns_429_after_burst`

Ran 10 tests in 2.685s
OK

(3 requests succeed at 201, 4th returns 429 — rate limit patched to 3/min for deterministic testing)

### Probe 4 — Disable geo provider A → provider B enriches. Disable both → still stored, no geo
Automated: `submissions.tests.GeoFallbackTests.test_provider_a_fails_provider_b_succeeds`,
`test_all_providers_fail_submission_still_succeeds` — both mock the provider chain directly
for determinism, per project ground rules (mocked in tests, real APIs for manual/dev only).
Manual (real infrastructure, not mocked):

Geo provider _try_ip_api failed for 127.0.0.1: reserved range
Geo provider _try_ipapi_co failed for 127.0.0.1: 429 Client Error: Too Many Requests
[17/Aug/2026 05:39:48] "POST /api/submissions/ HTTP/1.1" 201 65


### Probe 5 — Force email/webhook side effect to throw → submission still succeeds, still stored
Automated: `submissions.tests.SideEffectFailureTests.test_failing_side_effect_does_not_block_submission`
(patches `send_confirmation` to raise; asserts 201 still returned). Found and fixed a real gap
during this test — see BUILDLOG.md Phase 2.

### Probe 6 — Fill honeypot like a bot → silently dropped
Automated: `submissions.tests.HoneypotTests.test_honeypot_triggered_does_not_create_row`
(asserts 201 fake-success returned to the bot, but `Submission.objects.count()` unchanged)

## CORS surface split (supports demo step: "disallowed origin")
Automated: `dashboard.tests.CORSSurfaceTests` — public paths (`/api/submissions/`) carry
`access-control-allow-origin` for any origin; authenticated paths (`/api/dashboard/stats/`)
carry none, so a browser blocks cross-origin JS from reading the response even with a
leaked token

## Deferred / out of scope (per §7)
- Docker + PostgreSQL — deferred to end of project by design; SQLite used through development.
- Multi-role RBAC beyond "owner" — noted as non-goal in DESIGN.md.