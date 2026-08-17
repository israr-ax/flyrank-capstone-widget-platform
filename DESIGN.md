# Design — Embeddable Widget & Lead-Capture Platform

## Problem
Let a tenant (customer) create embeddable widgets, get a one-line <script> snippet,
and safely collect submissions from any website that embeds it — validated,
rate-limited, spam-filtered, geo-enriched, and shown in a dashboard.

## Data model
- Tenant — a customer account
- TenantMembership — user <-> tenant (many-to-many via membership, role-based)
- Widget — belongs to a tenant, has type/config/form_fields, versioned bundle
- Submission — belongs to a tenant + widget, stores payload + geo + side-effect status

## API surface (three request paths)
1. Owner (authenticated, JWT):
   POST /api/auth/token/, POST /api/auth/token/refresh/
   CRUD /api/widgets/
   GET  /api/dashboard/stats/

2. Customer site (public, cached, CORS):
   GET /widget.js
   GET /api/widgets/{id}/config/

3. Visitor (public, CORS, protected):
   POST /api/submissions/

## Embed flow
tenant creates widget -> gets <script src="/widget.js?id={id}">
-> customer pastes it -> browser loads widget.js -> widget.js fetches
/api/widgets/{id}/config/ -> renders form -> visitor submits ->
POST /api/submissions/ -> validate -> rate-limit + honeypot -> geo enrich
(fallback chain) -> store -> fire side effect (non-blocking) -> 201 response

## Non-goal
No real CDN/hosting/domain. No form-builder generality beyond 3 widget types.
No multi-role permissions beyond "owner" in Phase 1-3 (RBAC is out of scope).