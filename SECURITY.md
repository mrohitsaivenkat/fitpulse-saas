# FitPulse SaaS — Platform Security Architecture (Phase 3D)

This document specifies the authoritative security controls, access models, defensive mechanisms, and production operational hardening implemented across the FitPulse SaaS platform.

---

## 1. Authentication Model (Phase 3A)
- **Password Storage**: Cryptographic PBKDF2 with SHA-256 HMAC (600,000 rounds) via Werkzeug security primitives. Plaintext passwords are never persisted.
- **Constant-Time Verification**: Password verification uses constant-time string comparison (`hmac.compare_digest`) to defeat timing side-channel attacks.
- **Account State Verification**: Deactivated accounts (`is_active=False`) are blocked from authentication and API operations.
- **Anti-Enumeration**: Authentication rejections return generic `"Invalid email or password."` messages without disclosing whether an email exists in the platform.
- **Session Invalidation**: Clean session clearing upon logout via `session.clear()` and `logout_user()`.
- **Brute-Force Rate Limiting**: In-memory sliding-window throttling (`services/rate_limiter.py`) limits authentication endpoints (`/login`, `/register`) to prevent automated credential stuffing.

---

## 2. Role-Based Access Control (RBAC) (Phase 3B)
- **Authoritative Server Roles**: Supported roles are `SUPER_ADMIN`, `COACH`, and `CLIENT`.
- **Backend Verification**: User roles are read directly from the verified database record (`user.role`). Client cookies, form fields, and query parameters are never trusted.
- **Privilege Escalation Protection**: Public registration endpoints strictly force `role="COACH"`. Users cannot self-promote to `SUPER_ADMIN`.
- **Scoped Portals**:
  - `/admin/*` — Strictly restricted to `SUPER_ADMIN` via `@admin_required`.
  - `/coach/*` — Restricted to `COACH` via `@coach_required`.
  - `/client/*` — Restricted to `CLIENT` via `@client_required`.
- **Post-Login Routing & Open Redirect Defense**: Post-login redirect targets are strictly local (`/` prefix, blocking `//` protocol-relative and `https://` absolute URLs) and verified against the user's role boundary.

---

## 3. Multi-Tenant Authorization & Ownership Isolation (Phase 3C)
- **Tenant Hierarchy**: A `COACH` is a SaaS tenant; a `CLIENT` is an enrolled athlete belonging to exactly one coach.
- **Authoritative Tenant Identity**: `coach_id` is derived from `current_user.coach.id`; `client_id` is derived from `current_user.client.id`. Any `coach_id` or `client_id` submitted in request payloads is discarded.
- **Direct Object Reference (IDOR) Defense**: Before retrieving, modifying, or deleting resources (clients, diet plans, workout blocks, biometrics, transformations), backend ownership checkers verify tenant ownership.
- **Relational Traversal**: Entities without direct `coach_id` columns (e.g. `Progress`, `Measurement`, `ProgressPhoto`) are verified through parent relationships (`Progress -> Client -> Coach`).
- **Non-Disclosing Rejection**: Cross-tenant requests return generic HTTP 404/403 responses without disclosing whether the foreign tenant's record exists.

---

## 4. Media & File Upload Security (Phase 3D)
- **Physical Directory Separation**: The upload folder (`uploads/`) is stored outside the public `static/` directory.
- **Extension Whitelist**: Only `png`, `jpg`, `jpeg`, and `webp` are allowed. Executable scripts (`.php`, `.exe`, `.sh`, `.html`, `.svg`) are strictly rejected.
- **Path Traversal Defense**: Filenames are sanitized with `os.path.basename` and checked for `..` sequences.
- **Non-Predictable Storage Names**: Uploaded files receive cryptographically random UUID4 filenames.
- **Authenticated Media Streaming**: Private progress photos are served strictly via `GET /api/v1/media/photos/<id>` requiring authentication and athlete/coach ownership checks.

---

## 5. Session Security & CSRF Protection (Phase 3D)
- **Session Cookies**:
  - `SESSION_COOKIE_HTTPONLY = True` (mitigates XSS cookie theft).
  - `SESSION_COOKIE_SAMESITE = 'Lax'` (mitigates cross-site request forgery).
  - `SESSION_COOKIE_SECURE = True` in production environments.
- **CSRF Token Validation**:
  - State-changing operations (`POST`, `PUT`, `PATCH`, `DELETE`) require a valid session CSRF token.
  - Supports both HTML form field `csrf_token` and HTTP headers (`X-CSRF-Token`, `X-CSRFToken`).
  - Validated via constant-time `hmac.compare_digest`.

---

## 6. HTTP Security Headers
The following security headers are injected into all HTTP responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- `Content-Security-Policy`: Scoped to `'self'`, Google Fonts, and Chart.js.
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains` (enabled in production).

---

## 7. Audit & Forensics
- Forensic compliance is maintained via the `audit_logs` table.
- `sanitize_audit_text()` actively redacts passwords, tokens, API keys, and hashes before persistence.

---

## 8. Production Deployment Checklist
Prior to live production deployment:
1. Ensure `FLASK_ENV=production` is set in the runtime environment.
2. Provide a high-entropy random string for `SECRET_KEY` in environment variables.
3. Configure `DATABASE_URL` pointing to an encrypted PostgreSQL cluster.
4. Terminate TLS/HTTPS at the load balancer / reverse proxy.
5. Configure cloud object storage (e.g. Google Cloud Storage or S3) with signed URLs for high-volume media.
