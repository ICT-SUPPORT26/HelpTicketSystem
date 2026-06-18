---
name: Node.js backend architecture
description: Flask replaced by Express; architecture, auth, DB, password hashing decisions
---

# Node.js Backend Architecture

## Structure
- `backend/server.js` — Express entry, runs on port 8000
- `backend/routes/` — auth, tickets, categories, users, notifications, dashboard, reports
- `backend/middleware/auth.js` — requireAuth (JWT verify) + loadUser (fetch user row)
- `backend/db/pool.js` — pg Pool via DATABASE_URL
- `backend/db/schema.js` — CREATE TABLE IF NOT EXISTS + seed defaults
- `backend/services/notifications.js` — DB-only notifications (no email)
- `backend/utils/serializers.js` — toDict helpers for all models

## Auth
- JWT: access 30min, refresh 7 days. Secret = SESSION_SECRET env var.
- Payload uses `sub` field (string of user id).
- Tokens in localStorage; axios interceptor auto-refreshes on 401.

## Password Hashing
- Flask used Werkzeug `scrypt:327` format — incompatible with bcryptjs.
- **Why:** On first deploy, existing scrypt hashes must be replaced. `seedDefaults()` uses `ON CONFLICT DO UPDATE SET password_hash = CASE WHEN NOT LIKE '$2%' THEN <bcrypt> ELSE existing END` to auto-migrate scrypt → bcrypt.

## DB
- PG table for users is quoted `"user"` (reserved word).
- All tables use `CREATE TABLE IF NOT EXISTS`.

## Role Permissions
- admin: all access
- intern: only assigned tickets; status limited to open/in_progress/resolved
- user: own tickets only; no updates

## Vite Proxy
- `frontend/vite.config.js` proxies `/api` and `/uploads` to `http://localhost:8000`
