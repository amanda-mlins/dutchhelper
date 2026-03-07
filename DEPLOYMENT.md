# DutchHelper — Production Deployment Guide

**Stack:** FastAPI backend on Railway · Vue/Vite frontend on Netlify · PostgreSQL on Railway

---

## Prerequisites

- GitHub account (repo: `amanda-mlins/dutchhelper`)
- [Railway](https://railway.com) account (sign in with GitHub)
- [Netlify](https://netlify.com) account (sign in with GitHub)
- Google Cloud project with an OAuth 2.0 client (for Google login)
- OpenRouter API key

---

## Repository Layout

```
dutchhelper/
├── backend/          ← FastAPI app (deployed to Railway)
│   ├── app/
│   ├── migrations/   ← Alembic migrations (run automatically on deploy)
│   ├── requirements.txt
│   ├── Procfile      ← fallback start command
│   └── runtime.txt   ← python-3.13.0
├── frontend/         ← Vue/Vite app (deployed to Netlify)
│   ├── src/
│   ├── package.json
│   └── .env.production  ← set VITE_API_URL here before build
├── railway.json      ← Railway build + deploy config (repo root)
└── nixpacks.toml     ← Nixpacks build config (repo root)
```

---

## Part 1 — Backend on Railway

### 1.1 Create the Railway project

1. Go to [railway.com](https://railway.com) → **New Project**
2. Choose **"Deploy from GitHub repo"**
3. Select **`amanda-mlins/dutchhelper`**
4. Railway detects `railway.json` at the repo root automatically
5. Click **"Deploy Now"** — the first build will start

> The `railway.json` at the repo root controls everything:
> - **Build:** `pip install -r backend/requirements.txt`
> - **Start:** `cd backend && python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`
> - **Health check:** `GET /health` (must return 200 before traffic is routed)

### 1.2 Add PostgreSQL

1. Inside your Railway project → click **"+ Add Service"**
2. Choose **"Database"** → **"PostgreSQL"**
3. Railway automatically creates a `DATABASE_URL` variable and injects it into all services — **do not add it manually**

### 1.3 Generate your Railway backend URL

1. Click your backend service → **"Settings"** → **"Networking"**
2. Click **"Generate Domain"**
3. Note the URL — it will look like `https://dutchhelper-production.up.railway.app`

You will need this URL for the environment variables below and for Google OAuth.

### 1.4 Set environment variables

Click your backend service → **"Variables"** tab → add the following.  
Do **not** add `DATABASE_URL` — it is injected automatically by the PostgreSQL plugin.

| Variable | Value |
|---|---|
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `JWT_SECRET_KEY` | Output of `openssl rand -hex 32` — generate a **fresh** one, never reuse the dev key |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `ALLOWED_ORIGINS` | `["https://your-netlify-app.netlify.app"]` *(update after Netlify deploy)* |
| `FRONTEND_URL` | `https://your-netlify-app.netlify.app` *(update after Netlify deploy)* |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | `https://your-railway-app.railway.app/api/auth/google/callback` |

> **Generate a fresh JWT secret:**
> ```bash
> openssl rand -hex 32
> ```

### 1.5 Verify the backend is healthy

After the deploy succeeds, visit:

```
https://your-railway-app.railway.app/health
```

Expected response:
```json
{"status": "ok", "database": "reachable"}
```

If you see a 503, check the **"Deploy Logs"** tab — most likely a missing environment variable or a failed Alembic migration.

---

## Part 2 — Frontend on Netlify

### 2.1 Update the production env file

Edit `frontend/.env.production` and replace the placeholder with your real Railway URL:

```bash
VITE_API_URL=https://your-railway-app.railway.app
```

Commit and push this change before deploying to Netlify:

```bash
git add frontend/.env.production
git commit -m "chore: set production API URL"
git push
```

### 2.2 Create the Netlify site

1. Go to [netlify.com](https://netlify.com) → **"Add new site"** → **"Import an existing project"**
2. Choose **GitHub** → select **`amanda-mlins/dutchhelper`**
3. Set the **build settings**:

   | Setting | Value |
   |---|---|
   | Base directory | `frontend` |
   | Build command | `npm run build` |
   | Publish directory | `frontend/dist` |

4. Add an **environment variable** under Site settings → Environment variables:

   | Variable | Value |
   |---|---|
   | `VITE_API_URL` | `https://your-railway-app.railway.app` |

   > This overrides `.env.production` at build time if needed.

5. Click **"Deploy site"**

### 2.3 Note your Netlify URL

After deploy, Netlify gives you a URL like `https://dutchhelper.netlify.app`.  
You can configure a custom domain under **Domain settings**.

### 2.4 Update Railway with the Netlify URL

Go back to Railway → backend service → **Variables** and update:

| Variable | New value |
|---|---|
| `ALLOWED_ORIGINS` | `["https://your-netlify-app.netlify.app"]` |
| `FRONTEND_URL` | `https://your-netlify-app.netlify.app` |

Railway will redeploy automatically.

---

## Part 3 — Google OAuth

In [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials → your OAuth 2.0 client:

**Authorised JavaScript origins** — add:
```
https://your-netlify-app.netlify.app
```

**Authorised redirect URIs** — add:
```
https://your-railway-app.railway.app/api/auth/google/callback
```

> The redirect URI must match `GOOGLE_REDIRECT_URI` in Railway **exactly** — including the `https://` and no trailing slash.

---

## Part 4 — Database Migrations

Migrations run **automatically** on every deploy via the start command:

```
python -m alembic upgrade head
```

To run migrations manually (e.g. to check status):

```bash
# From the Railway CLI (install with: npm i -g @railway/cli)
railway run --service <service-name> python -m alembic current
railway run --service <service-name> python -m alembic history
```

To generate a new migration after changing `models.py`:

```bash
# Locally, with your dev DATABASE_URL active
cd backend
alembic revision --autogenerate -m "describe_your_change"
git add migrations/versions/
git commit -m "feat: add migration for <change>"
git push
# Railway will run `alembic upgrade head` on next deploy
```

---

## Part 5 — Redeployment

| Trigger | What happens |
|---|---|
| `git push` to `main` | Railway and Netlify both redeploy automatically |
| Environment variable change in Railway | Railway redeploys the backend service automatically |
| Environment variable change in Netlify | Trigger a manual redeploy from Netlify dashboard |

---

## Troubleshooting

### Backend won't start
- Check **Deploy Logs** in Railway for the full traceback
- Most common cause: missing or invalid environment variable (especially `JWT_SECRET_KEY`)
- The app will refuse to start if `JWT_SECRET_KEY` is a placeholder — generate a real one with `openssl rand -hex 32`

### `/health` returns 503
- Database is unreachable — check that the PostgreSQL plugin is attached and `DATABASE_URL` is injected
- Check that the Alembic migration ran successfully in the deploy log

### CORS errors in the browser
- `ALLOWED_ORIGINS` in Railway must exactly match the Netlify URL (including `https://`, no trailing slash)

### Google OAuth redirect mismatch
- `GOOGLE_REDIRECT_URI` in Railway must exactly match the URI registered in Google Cloud Console

### Frontend shows blank page or API errors
- Check that `VITE_API_URL` is set correctly in Netlify's environment variables
- Trigger a fresh Netlify deploy after updating the variable

---

## Local Development

```bash
# Backend
cd backend
cp .env.example .env          # fill in your local values
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev                   # proxies /api to localhost:8000 via vite.config.js
```

The Vite dev proxy is configured in `frontend/vite.config.js` and handles `/api` → `http://localhost:8000` automatically, so no `VITE_API_URL` is needed locally.

---

## Environment Variable Reference

See `backend/.env.example` for a full annotated list of all supported variables with defaults.
