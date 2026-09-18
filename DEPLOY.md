# Deploying the IFDC API to Railway

The API is a FastAPI app served by uvicorn. Railway builds it with Nixpacks
(Python 3.13 from `.python-version`, packages from `requirements.txt`) and runs
the command in `railway.json`.

## 1. Push this folder to GitHub

This folder is already a git repository with one commit. `.env`, `venv/` and
`uploads/` are ignored, so no passwords or local files are published.

```bash
git remote add origin https://github.com/<your-account>/IFDC-Backend.git
git push -u origin main
```

Make the GitHub repository **private** – the code is not secret, but a private
repo keeps the project tidy.

## 2. Create the Railway project

1. On railway.app: **New Project → Deploy from GitHub repo** and pick the repo.
2. If these files are in a `backend/` folder inside the repo rather than at its
   top level, open the service → **Settings → Build → Root Directory** and set it
   to `backend`. Without this the build fails with "Railpack failed to prepare
   the build", because Railway looks for the app at the top of the repo.
3. In the same project: **New → Database → Add PostgreSQL**.
4. Open the API service → **Settings → Networking → Generate Domain**. This
   gives the public URL, e.g. `https://ifdc-api.up.railway.app`.

## 3. Add a volume for uploaded files

API service → **Settings → Volumes → New Volume**, mount path `/data`.

Uploaded images and PDFs are written there and survive redeploys. On the first
start the app copies the files in `uploads_seed/` onto the empty volume, so
existing blogs, news posts and annual reports keep their images.

## 4. Environment variables

API service → **Variables**:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference the Postgres service) |
| `UPLOAD_DIR` | `/data` |
| `JWT_SECRET` | a long random string – **not** the local one |
| `ADMIN_EMAIL` | `admin@ifdchild.org` |
| `ADMIN_PASSWORD` | a strong password (used only if the admin user does not exist yet) |
| `ALLOWED_ORIGINS` | the public site and dashboard URLs, comma separated |
| `ADMIN_DASHBOARD_URL` | the deployed dashboard URL |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `SMTP_FROM` `ADMIN_NOTIFY_EMAIL` | Gmail SMTP settings and App Password, for donation notifications |

`PORT` is provided by Railway – do not set it.

## 5. Copy the existing content into the Railway database

The tables are created automatically on first start, but the blogs, news posts,
resources and users come from the local database.

1. Railway → Postgres service → **Variables** → copy `DATABASE_PUBLIC_URL`.
2. Run, from this folder:

```bash
venv/Scripts/python.exe scripts/restore_to_railway.py "<DATABASE_PUBLIC_URL>"
```

The script dumps the local database and loads it into Railway, replacing any
tables of the same name. Run it only while the site is not yet live, or it will
overwrite content added through the deployed dashboard.

## 6. Point the website and dashboard at the API

In the website (`IFDC`) and dashboard (`IFDC-Admin`) set the API base URL to the
Railway domain and redeploy them. Then add those site URLs to `ALLOWED_ORIGINS`
above.

## Checks after deploying

- `https://<domain>/health` returns `{"status":"ok"}`
- `https://<domain>/api/news` lists the news posts
- `https://<domain>/uploads/<some-file>.jpg` shows an image
- Log in to the dashboard, add a test post, redeploy, and confirm it is still
  there (database and volume both persist).
