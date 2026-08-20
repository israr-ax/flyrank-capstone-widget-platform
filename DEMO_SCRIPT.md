# Demo Script — FlyRank Capstone Widget Platform

Follow these steps in order for the 6-minute demo. Each step is copy-pasteable.
Commands assume Windows `cmd.exe`. On Linux/Mac, replace `\"` escaping with normal
quotes and use `for i in 1 2 3 4 5 6 7 8 9 10 11 12; do ... ; done` instead of `for /L`.

## Setup (before recording — not part of the timed demo)

**Terminal 1 — API server:**
```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
Note the widget ID printed by `seed_demo` — you'll need it below. Call it `<WIDGET_ID>`.

**Terminal 2 — fake customer site (different origin, port 5500):**
```bash
cd customer-site
python -m http.server 5500
```

**Browser**: open `http://localhost:5500` (don't submit the form yet).

**Get a token** (Terminal 3, keep this open for the whole demo):
```bash
curl -X POST http://localhost:8000/api/auth/token/ -H "Content-Type: application/json" -d "{\"username\": \"demoowner\", \"password\": \"demopass123\"}"
```
Copy the `access` token — call it `<TOKEN>` below.

---

## Step 1 — Create a widget through the authenticated API (0:00–0:50)

```bash
echo {"widget_type": "signup_form", "title": "Join our newsletter", "description": "Get weekly updates", "form_fields": [{"name": "email", "type": "email", "required": true}], "button_text": "Subscribe"} > widget.json
```
```bash
curl -X POST http://localhost:8000/api/widgets/ -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d @widget.json
```
Show the returned `id` and say the embed snippet:
```html
<script src="http://localhost:8000/widget.js" data-widget-id="<returned-id>"></script>
```

## Step 2 — Open the customer site, different origin (0:50–1:30)

Refresh `http://localhost:5500`. Point out: different port (5500 vs 8000), plain HTML,
the widget script wasn't hand-built into this page.

## Step 3 — Submit the form, show the dashboard (1:30–2:30)

Fill and submit the form in the browser → "Thanks! Received."

```bash
curl http://localhost:8000/api/dashboard/stats/ -H "Authorization: Bearer <TOKEN>"
```
Point out the submission count went up.

## Step 4 — Attack yourself (2:30–4:00)

**Invalid payload:**
```bash
curl -X POST http://localhost:8000/api/submissions/ -H "Content-Type: application/json" -d "{\"widget_id\": \"<WIDGET_ID>\", \"data\": {}}"
```
→ clean `400` with a JSON error, not a 500.

**Disallowed origin (CORS):**
```bash
curl -X OPTIONS http://localhost:8000/api/dashboard/stats/ -H "Origin: http://evil-site.com" -H "Access-Control-Request-Method: GET" -i
```
→ no `access-control-allow-origin` header in the response. Say: *"No CORS headers on
admin endpoints — a browser blocks this before it even reaches our auth check."*

**Burst / rate limit** — save this as `burst_test.bat` in the repo root and run it
(interactive `for /L` in cmd.exe needs single `%`, but a `.bat` file needs `%%`,
hence the separate script):
```bat
@echo off
echo {"widget_id": "<WIDGET_ID>", "data": {"email": "burst@example.com"}, "hp_field": ""} > submission.json
for /L %%i in (1,1,12) do curl -s -o nul -w "%%i: %%{http_code}\n" -X POST http://localhost:8000/api/submissions/ -H "Content-Type: application/json" -d @submission.json
```
```bash
burst_test.bat
```
→ first ~10 requests return `201`, then `429` appears. Point out a normal request
right after still succeeds (rate limit resets, doesn't lock you out permanently).

## Step 5 — Kill geo provider A live (4:00–4:45)

Edit `submissions/enrichment.py` — comment out the first provider:
```python
PROVIDERS = [_try_ipapi_co]  # _try_ip_api temporarily "down" for the demo
```
Server auto-reloads. Submit another form response on `http://localhost:5500`.
Say: *"Provider A is down, provider B took over — no code change needed at the
call site to handle this."*

**Revert immediately after:**
```bash
git checkout -- submissions/enrichment.py
```

## Step 6 — Break the side effect (4:45–5:20)

Edit `submissions/side_effects.py`:
```python
def send_confirmation(submission):
    raise Exception("simulated SMTP outage")
```
Server auto-reloads. Submit another form response — still `201`.
Say the exact sentence: **"Non-critical failures never break the main path."**

**Revert immediately after:**
```bash
git checkout -- submissions/side_effects.py
```

## Step 7 — Close on the dashboard (5:20–6:00)

```bash
curl http://localhost:8000/api/dashboard/stats/ -H "Authorization: Bearer <TOKEN>"
```
Say: *"This application safely accepts data from websites I don't own — validated,
rate-limited, spam-filtered, resilient to dependency failure, and every submission
is correctly attributed to the right tenant."*

---

## After recording — sanity check

```bash
git status
git diff submissions/enrichment.py submissions/side_effects.py
```
Both should show no changes (confirms the live edits were fully reverted).

```bash
python manage.py test
```
All tests should still pass — confirms the demo didn't leave the codebase in a broken state.