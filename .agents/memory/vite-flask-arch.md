---
name: Single-server Flask+React architecture
description: How Flask serves the built React SPA — the correct setup for this Replit project to avoid proxy timeouts
---

## Rule
Always serve the React build from Flask. Never use the Vite dev server as the webview.

**Why:** Replit's janeway proxy doesn't support WebSocket upgrades. Vite's HMR retries with polling mode which floods connections and causes ERR_CONNECTION_TIMED_OUT for external users.

## Architecture
- Flask runs on `0.0.0.0:5000` (webview port)
- React is built into `frontend/dist` via `cd frontend && npm run build`
- `app.py` has a `@app.before_request` hook `_serve_react()` that intercepts all non-API/non-static paths and serves `frontend/dist/index.html` (SPA fallback)
- API calls from React use relative paths `/api/v1/*` — same server, no proxy needed
- Only one workflow: "Backend" (`python main.py`, webview, port 5000)

## How to apply
- After frontend code changes: run `cd frontend && npm run build` then restart Backend workflow
- Do NOT re-add a Vite dev server workflow as the webview
- CORS is still configured for `/api/v1/*` but same-origin requests won't need it
