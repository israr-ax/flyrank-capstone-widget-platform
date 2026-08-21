# FlyRank Capstone — Embeddable Widget & Lead-Capture Platform

A backend platform that lets a tenant create embeddable lead-capture widgets, get a
one-line `<script>` snippet, and safely collect submissions from any website that embeds
it — validated, rate-limited, spam-filtered, geo-enriched, and visible in a dashboard.

## Architecture

┌─────────────────┐ ┌──────────────────────────────────────┐
│ Customer Site │ │ Django + DRF API │
│ (any origin) │ │ │
│ │ GET │ /widget.js ─────────────────────┐ │
│ <script src= │────────►│ │ │
│ widget.js> │ │ /api/widgets/{id}/config/ (cached) │
│ │ │ │ │
│ [Shadow DOM] │ GET │ ▼ │
│ renders form │◄────────│ widgets app │
│ │ │ │
│ visitor submits │ POST │ /api/submissions/ │
│ │────────►│ │ │
└──────────────────┘ │ ▼ │
│ submissions app │
│ - validation │
│ - rate limit (per IP + per widget) │
│ - honeypot │
│ - geo fallback (provider A → B) │
│ - fail-soft side effect │
│ │ │
│ ▼ │
│ PostgreSQL/SQLite (tenant-scoped) │
└──────────────────────────────────────┘
▲
│ JWT auth
┌─────────┴──────────┐
│ Widget Owner │
│ (dashboard, CRUD) │
└───────────────────────┘


**Apps**: `accounts` (tenant + auth), `widgets` (CRUD + public config), `submissions`
(hardened public intake), `dashboard` (tenant-scoped stats).

**Tenant isolation**: every query touching widgets/submissions is scoped through a
single shared helper (`accounts.utils.get_tenant_for_user`) — proven by automated tests,
not just code review.

**CORS**: split by path, not by origin allow-list. `/widget.js`, `/api/widgets/{id}/config/`,
and `/api/submissions/` are open to any origin (required — customer sites are unknown in
advance). All other endpoints (auth, CRUD, dashboard) get no CORS headers, so browsers
block cross-origin JS from reading their responses even with a leaked token.

## Clone Repo
git clone https://github.com/israr-ax/flyrank-capstone-widget-platform
cd flyrank-capstone-widget-platform

## Run it

**Requires Docker Desktop.**

```bash
cp .env.example .env
docker compose up
```

First run builds the image and starts Postgres + Django (a few minutes). Migrations run
automatically on container start. Once you see `Starting development server at 0.0.0.0:8000`,
open a second terminal:

```bash
docker compose exec web python manage.py seed_demo
```

Server runs at `http://localhost:8000`.

### Running tests

```bash
docker compose exec web python manage.py test
```

### Local (non-Docker) development

SQLite works too, if you'd rather not use Docker for day-to-day development:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then set DATABASE_URL=sqlite:///db.sqlite3
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Server runs at `http://localhost:8000`.

## Seed / demo data

```bash
python manage.py seed_demo
```

Creates:
- Owner login: `demoowner` / `demopass123`
- One tenant ("Demo Co") with one widget ("Demo Newsletter Signup")
- 3 demo submissions

The command prints the widget ID and a ready-to-use embed snippet.

## Try the cross-origin embed

A plain HTML test page (kept outside this repo, since it's a manual testing artifact,
not a deliverable) simulates a real customer site:

```html
<script src="http://localhost:8000/widget.js" data-widget-id="<seeded-widget-id>"></script>
```

Serve it from a different port (e.g. `python -m http.server 5500`) to prove real
cross-origin behavior — the widget renders inside a Shadow DOM, immune to the host
page's CSS.

## Run tests

```bash
python manage.py test
```

24 tests covering: CORS (public vs restricted), payload validation, oversized payload,
honeypot, rate limiting, geo fallback (both branches), fail-soft side effects, widget
config + caching, tenant isolation (widgets + dashboard), successful widget rendering.

## Limitations (honest, by design — see `DESIGN.md`)

- SQLite used through development; PostgreSQL + Docker Compose added at the very end of
  the project, not from day one (a deliberate sequencing choice, not an oversight).
- No real CDN/hosting for `widget.js` — served directly by Django (fine for this scope;
  a production version would put it behind a CDN with long cache + hashed filename).
- Only one role ("owner") per tenant — no granular RBAC.
- Only 3 widget types supported (signup_form, cta, popover) — not a general form builder.
- Geo enrichment uses 2 free providers (ip-api.com, ipapi.co); both reliably fail for
  private/reserved IPs like `127.0.0.1` — this is expected and is exactly what proves the
  fallback-to-empty-geo path works, not a bug.

## AI usage

See `BUILDLOG.md` for a phase-by-phase log of where AI helped, what broke, and what was
corrected.

run: docker compose up

seed: docker compose exec web python manage.py seed_demo

test: docker compose exec web python manage.py test