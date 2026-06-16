---
name: React migration architecture
description: Two-workflow setup for ICT Helpdesk — Flask backend on 8000, React Vite on 5000.
---

## Architecture

- **Flask backend**: `python main.py` → port 8000, workflow "Start application" (console)
- **React Vite frontend**: `cd frontend && npm run dev` → port 5000, workflow "Start Frontend" (webview)
- **JWT**: access token 60min, refresh token 7 days, stored in localStorage
- **Vite proxy**: `/api/*` → `http://localhost:8000`, `/uploads/*` → `http://localhost:8000`

## Key files
- `api_routes.py` — all JSON API endpoints, Blueprint at `/api/v1/`
- `frontend/src/api/client.js` — Axios instance with auto-refresh interceptor
- `frontend/src/context/AuthContext.jsx` — user state + login/logout
- `frontend/vite.config.js` — proxy config and port 5000

## Auth quirk
- Admin default: username=`215030`, password=`admin123` (hardcoded check in `api_routes.py` login)
- Intern default: username=`dctraining`, password=`Dctraining2023` (same)
- Regular users: standard password_hash check

## CSRF exemption
`csrf.exempt(api_bp)` called in `app.py` **before** `app.register_blueprint(api_bp)`.
JWT tokens serve as CSRF protection for the API blueprint.

**Why:** CSRFProtect is applied globally to the Flask app. The API blueprint must be exempted because React sends JWT Bearer tokens, not CSRF form tokens. Order matters — exempt before register.
