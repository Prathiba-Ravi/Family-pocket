# Deployment Guide

This repo is split into two apps:

- `backend/`: Flask API with SQLite
- `frontend/`: Vite React client

## Backend

Use a production WSGI server such as `gunicorn`.

### Render backend service

Create a Render Web Service from the repository root with these values:

- Build command: `cd backend && pip install -r requirements.txt`
- Start command: `cd backend && gunicorn wsgi:app`
- Runtime: Python 3
- Disk mount: `/var/data`
- Persistent database path: `/var/data/guardian_ledger.db`

Environment variables:

```ini
SECRET_KEY=replace-with-a-long-random-value
FLASK_ENV=production
DATABASE_PATH=/var/data/guardian_ledger.db
CORS_ORIGINS=https://your-frontend-domain
VULNERABLE_MODE=true
LOG_LEVEL=INFO
```

If you want the secure build instead, change `VULNERABLE_MODE` back to
`false`.

Start command:

```bash
cd backend
pip install -r requirements.txt
gunicorn wsgi:app
```

Environment variables:

```ini
SECRET_KEY=replace-with-a-long-random-value
FLASK_ENV=production
DATABASE_PATH=/var/data/guardian_ledger.db
CORS_ORIGINS=https://your-frontend-domain
VULNERABLE_MODE=false
LOG_LEVEL=INFO
```

### Demo deployment with vulnerabilities enabled

If you want the presentation build to expose the intentionally insecure
behavior, set:

```ini
VULNERABLE_MODE=true
```

Keep the other values the same, especially `SECRET_KEY`, `DATABASE_PATH`,
and `CORS_ORIGINS`. This should only be used for a closed demo or lab
environment.

Notes:

- `DATABASE_PATH` must point to persistent storage if you want data to survive restarts.
- `CORS_ORIGINS` must include the exact frontend origin.
- Keep `VULNERABLE_MODE=false` for production.

## Frontend

Build the Vite app with the backend URL injected at build time.

```bash
cd frontend
npm install
VITE_API_URL=https://your-backend-domain npm run build
```

Deploy the generated `frontend/dist` folder to any static host.

## Recommended deployment split

1. Deploy the backend first.
2. Copy the backend public URL into `VITE_API_URL`.
3. Build and deploy the frontend.
4. Update `CORS_ORIGINS` on the backend to allow the frontend domain.

## Local production-style test

Backend:

```bash
cd backend
gunicorn wsgi:app
```

Frontend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:5000 npm run build
```

## Exact demo deployment order on Render

1. Create the backend Web Service first.
2. Attach a persistent disk and set `DATABASE_PATH` to the mounted path.
3. Set `VULNERABLE_MODE=true` in the backend environment.
4. Copy the backend public URL.
5. Build the frontend with `VITE_API_URL` set to that backend URL.
6. Deploy the frontend as a static site.
7. Update `CORS_ORIGINS` on the backend to the exact frontend domain.