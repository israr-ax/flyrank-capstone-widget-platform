# Build Log — FlyRank Capstone

Format: what AI generated → what I changed/corrected → why.

---

## Phase 1 · Design

- AI proposed Django + DRF scaffold with 4 apps (accounts, widgets, submissions, dashboard),
  separate Tenant/TenantMembership models (chose this over built-in User=tenant for flexibility),
  and JWT auth via simplejwt (chose over DRF token auth for statelessness on public-facing API).

## Phase 2 · Hardened Submission Path

- AI generated the submission serializer, throttle classes, geo enrichment fallback chain,
  side-effect hook, and view.
- **Bug found via testing**: `send_confirmation` was called without an outer try/except in the
  view. It has its own internal try/except, but a test that force-raised an exception from it
  (mocking past the internal guard) proved the *view* itself wasn't protected — a genuinely
  misbehaving side-effect function could 500 an otherwise-successful submission. Fixed by wrapping
  the call site in `views.py` with its own try/except, not just relying on the function's internal one.
- **Test infra issue #1**: DRF's per-IP/per-widget throttle state is stored in Django's cache
  framework, which is NOT reset automatically between test methods (only the DB rolls back).
  Tests were bleeding throttle counts into each other. Fixed with `cache.clear()` in `setUp()`.
- **Test infra issue #2**: `@override_settings(REST_FRAMEWORK=...)` did not actually change the
  throttle rate used during a test. Root cause: DRF's `SimpleRateThrottle.THROTTLE_RATES` is
  evaluated once at class-definition/import time — it's a static snapshot of
  `api_settings.DEFAULT_THROTTLE_RATES`, not something that re-reads Django settings per-request.
  `override_settings` changes Django's settings object but not the already-bound class attribute.
  Fixed by patching `SubmissionIPThrottle.THROTTLE_RATES` / `SubmissionWidgetThrottle.THROTTLE_RATES`
  directly with `unittest.mock.patch.object` instead of relying on settings override.
- Manual curl testing on Windows cmd.exe hit two environment issues (not code bugs): `\` line
  continuation isn't supported in cmd.exe (bash-only syntax), and literal `<>` placeholder brackets
  were accidentally left in a widget_id. Solved by using `-d @file.json` for payloads going forward.

---

## Phase 3 · Delivery / Dashboard / Proof

- AI generated: registration/login flow, `get_tenant_for_user` shared helper (chosen to centralize
  tenant resolution so it can't be reimplemented inconsistently across views), Widget CRUD ViewSet
  with tenant filtering entirely inside `get_queryset`, cached public config endpoint (ETag tied to
  bundle_version + updated_at for automatic invalidation), Shadow-DOM-based widget.js, tenant-scoped
  dashboard stats.
- Decision: Shadow DOM over inline styles for widget.js — verified with a deliberately CSS-clashing
  fake customer page (yellow/red-bordered inputs) to prove real isolation, not just assume it.
- Tenant isolation was NOT just manually assumed — wrote explicit tests (list/retrieve/update/delete/
  create + dashboard aggregation) proving tenant A can never see, modify, or delete tenant B's data,
  even with a valid JWT. This is the ground-rule ("multi-tenant isolation is non-negotiable") made
  concrete and testable rather than just a code review checklist item.

## Docker + PostgreSQL Migration

- AI generated Dockerfile, docker-compose.yml, docker-entrypoint.sh (wait-for-db loop +
  migrate + runserver), and DATABASE_URL parsing via dj-database-url.
- **Bug**: `docker-entrypoint.sh` failed with `no such file or directory` — misleading
  error. Initially suspected Windows CRLF line endings (a known cross-platform issue) and
  added `.gitattributes` to force LF — this did NOT fix it.
- **Actual root cause**, found by inspecting the file's raw bytes inside the container
  with `od -c`: the file had a **UTF-8 BOM** (`EF BB BF`) at the very start, inserted by
  PowerShell's default `[System.Text.Encoding]::UTF8` when regenerating the file. The BOM
  sits before `#!/bin/bash`, so the Linux kernel can't parse the shebang line at all —
  same misleading "no such file" error as a bad shebang path.
  Fixed by using `New-Object System.Text.UTF8Encoding($false)` to write the file without
  a BOM. Confirmed with `od -c` showing the shebang as the literal first bytes.
- Lesson: "no such file or directory" on a script that visibly exists is a shebang-parsing
  symptom, not necessarily a missing-file problem — check for both CRLF *and* BOM.
- Ran the full test suite against real PostgreSQL (not just SQLite) to catch any DB-specific
  behavior differences — all 22 tests passed unchanged.