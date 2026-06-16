---
name: React migration architecture
description: Two-workflow setup for ICT Helpdesk — Flask backend on 8000, React Vite on 5000.
---

## Architecture

- **Flask backend**: `python main.py` → port 8000, workflow "Start application" (console)
- **React Vite frontend**: `cd frontend && npm run dev` → port 5000, workflow "Start Frontend" (webview)
- **JWT**: access token 60min, refresh token 7 days, stored in localStorage
- **Vite proxy**: `/api/*` → `http://localhost:8000`, `/uploads/*` → `http://localhost:8000`
- **CORS**: restricted to `http://localhost:5000` by default; override via `CORS_ORIGINS` env var (comma-separated)

## Key files
- `api_routes.py` — all JSON API endpoints, Blueprint at `/api/v1/`
- `frontend/src/api/client.js` — Axios instance with auto-refresh interceptor
- `frontend/src/context/AuthContext.jsx` — user state + login/logout
- `frontend/vite.config.js` — proxy config and port 5000

## Access control rules enforced in api_routes.py
- Users: read/comment/close their own tickets only
- Interns: update/escalate/comment only on tickets assigned to them; status limited to open/in_progress/resolved
- Admins: full access to all tickets and user management

## CSRF exemption
`csrf.exempt(api_bp)` called in `app.py` **before** `app.register_blueprint(api_bp)`.
JWT tokens serve as CSRF protection for the API blueprint.

**Why:** CSRFProtect is applied globally to the Flask app. The API blueprint must be exempted because React sends JWT Bearer tokens, not CSRF form tokens. Order matters — exempt before register.

## ticket_to_dict includes created_by_id
The `ticket_to_dict` serializer explicitly includes `created_by_id` (an integer) alongside the nested `creator` object. Both are available in the React frontend for permission checks without requiring string coercion.

**Why:** `TicketDetail.jsx` needs a direct integer comparison for comment/close permissions; relying only on nested `creator.id` caused a bug when `creator` was null.
