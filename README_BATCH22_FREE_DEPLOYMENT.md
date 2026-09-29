# CareSphere Batch 22 — $0 Deployment Package

Purpose: deploy the already-tested CareSphere application with $0 recurring platform cost, using only free tiers and preserving application logic.

## Architecture

- Source control: GitHub Free
- Frontend: Cloudflare Pages (static Vite build)
- API: Render Free Python web service
- Database: Neon Free PostgreSQL
- AI: Google Gemini API free tier

This replaces the Batch21 assumption of Render-hosted Postgres. Render's current Free Postgres expires after 30 days; Batch22 therefore uses Neon for the database instead. Render Free web services are suitable for testing/hobby/preview use, not production-grade healthcare workloads. See the deployment notes below.

## What is inside this patch

- `backend/config.py` — CORS-aware settings; Gemini is the $0 example provider/model.
- `backend/.env.example` — production environment template using Neon + Gemini.
- `backend/main_cors.py` — safe helper for the CORS change in `app/main.py`.
- `render.yaml` — Render Free API only; NO Render database resource.
- `frontend/api_client.ts` — environment-driven production API base URL.
- `frontend/.env.example` — Vite production API variable.
- `frontend/public/_redirects` — SPA fallback for Cloudflare Pages.
- `diffs/*` — focused changes only.
- `optional/.gitignore.additions` — add these rules only if your existing `.gitignore` does not already cover secrets.

## Do not replace the working application

This is an infrastructure patch. Do not replace the whole frontend or backend with this archive.

Your working application files remain the source of truth for:

- authentication and RBAC
- patient registration
- assessments and deterministic risk logic
- Clinical Review
- AI clinical summary and AI decision support
- report generation, clinician recommendation, review, approval and release
- patient portal and reviewed status
- admin functions
- care gaps, follow-ups, notifications and audit logs

## Important $0 constraints

Render Free web services spin down after 15 minutes without inbound traffic and take about one minute to wake. Render grants 750 free instance hours/month per workspace. Render states that Free instances are not for production applications. If you have no payment method and would otherwise incur charges, Render says it disables services for the current billing period instead of billing you.

Cloudflare Pages static asset requests are free and unlimited on its free/paid plans when the request does not invoke Functions.

Neon Free currently includes 10 projects, 50 CU-hours/month per project, 0.5 GB storage/project and 5 GB egress/month.

GitHub Free is $0/month and includes unlimited public/private repositories.

Google's Gemini API currently exposes free-tier pricing for current Flash models. The example below uses `gemini-3.8-flash`; keep AI usage within the free tier and do not attach paid billing for this $0 setup.

## Before you start

1. Keep your tested CareSphere project in a local folder.
2. Make one local backup copy of that project folder.
3. Apply only the small deployment changes described below.
4. Do not commit `.env` files, database URLs with passwords, `SECRET_KEY`, or `AI_API_KEY`.

## Step 1 — Create the GitHub repository

Create a new GitHub repository named something like `CareSphere`.

Recommended repository shape:

```
CareSphere/
  frontend/
    package.json
    src/
    public/
  backend/
    app/
    requirements.txt
    .python-version
  render.yaml
```

Copy your current tested CareSphere source into that repository.

Then apply Batch22:

- copy `backend/config.py` to `backend/app/config.py` only if your working file still lacks `cors_origins` (preserve the rest of the working file)
- use the CORS helper/diff to update `backend/app/main.py`
- copy `frontend/api_client.ts` to `frontend/src/api/client.ts`
- copy `frontend/.env.example` into the frontend as the example template
- copy `frontend/public/_redirects` into `frontend/public/_redirects`
- copy `render.yaml` to the repository root

Commit and push.

## Step 2 — Create the Neon free database

Open Neon and create a new project.

Use the Free plan.

Create a database named `caresphere` if the console asks for a database name.

Open the project's Connect / connection details and copy a PostgreSQL connection string. Keep it private.

Important: a fresh Neon database starts empty. CareSphere's normal startup creates the SQLAlchemy tables, but it does not copy your local rows into Neon. For the simplest first deployment, use this as a fresh demo/test database. See the data-migration note near the end if you need existing local data.

## Step 3 — Create the Render Free API

In Render:

1. Connect your GitHub account.
2. Choose **New → Blueprint** if you want Render to read the repository's `render.yaml` automatically, or **New → Web Service** to enter the same settings manually.
3. Use the `caresphere-api-free` service from `render.yaml`.
4. Runtime: Python.
5. Root directory: `backend`.
6. Build command: `pip install -r requirements.txt`.
7. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
8. Health check: `/health`.
9. Plan: **Free**.

### Render environment variables

Set these values in the Render service settings:

`DATABASE_URL`

Paste the exact Neon PostgreSQL connection string.

`SECRET_KEY`

Render generates this automatically from the `generateValue: true` entry. If you are entering settings manually, generate a long random secret.

`CORS_ORIGINS`

Use the final Cloudflare Pages URL after Step 4, for example:

`https://caresphere.pages.dev`

For the first API-only deploy, you may temporarily leave this blank because local origins are still allowed. Update it after Cloudflare Pages is live.

`AI_ENABLED`

`true`

`AI_PROVIDER`

`gemini`

`AI_MODEL`

`gemini-3.8-flash`

`AI_API_KEY`

Paste the Gemini API key from Step 5.

`AI_BASE_URL`

`https://generativelanguage.googleapis.com/v1beta/openai/`

`AI_TIMEOUT_SECONDS`

`30`

`AI_MAX_OUTPUT_TOKENS`

`1200`

Deploy the API.

## Step 4 — Verify the API before deploying the frontend

Open:

`https://YOUR-RENDER-SERVICE.onrender.com/health`

You should receive JSON similar to:

```
{
  "status": "healthy",
  "service": "CareSphere API"
}
```

Also open:

`https://YOUR-RENDER-SERVICE.onrender.com/docs`

FastAPI's Swagger UI should load.

If `/health` fails, do not continue to Cloudflare Pages; fix the Render deployment first.

## Step 5 — Create the Gemini API key for the free tier

Open Google AI Studio and create a Gemini API key.

For this $0 architecture use the Gemini free tier only. The current Gemini documentation shows free-tier pricing for Flash models, and Google's OpenAI-compatibility endpoint is:

`https://generativelanguage.googleapis.com/v1beta/openai/`

The current example model is:

`gemini-3.8-flash`

Do not put the API key in GitHub or in the frontend. It belongs only in Render's server-side environment variables.

After adding `AI_API_KEY` and the other AI values in Render, redeploy the API if Render does not automatically redeploy.

## Step 6 — Deploy the Vite frontend to Cloudflare Pages

In Cloudflare:

1. Open **Workers & Pages**.
2. Choose **Create application → Pages**.
3. Choose **Connect to Git**.
4. Connect your GitHub account and select the CareSphere repository.
5. Set the project root directory to `frontend`.
6. Build command: `npm run build`.
7. Build output directory: `dist`.
8. Set environment variable:

`VITE_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com`

9. Deploy.

Cloudflare Pages will publish the site at a `*.pages.dev` URL.

The included `frontend/public/_redirects` provides the SPA fallback for deep links such as `/reports`, `/patients`, `/clinical-review`, and `/patient-portal`.

## Step 7 — Lock the API CORS to the Cloudflare URL

Copy your final Pages URL, for example:

`https://caresphere.pages.dev`

In Render → CareSphere API → Environment, set:

`CORS_ORIGINS=https://caresphere.pages.dev`

Save and redeploy the API.

Do not add a trailing slash.

If you later add another legitimate frontend origin, use comma-separated values:

`https://caresphere.pages.dev,https://your-other-origin.example`

## Step 8 — First login / initial data

A fresh Neon database will contain the database schema after the API starts, but it will not automatically contain your old local users or patient records unless you migrate them.

For a fresh demo/test deployment, create a patient through the existing CareSphere patient registration flow.

For clinician/administrator accounts, use your existing project provisioning mechanism or migrate existing user rows into Neon. Do not invent credentials in the frontend.

If you need to preserve the exact local users/patients/reports, stop here before entering real data and perform a planned database migration rather than manually recreating clinical records.

## Step 9 — Smoke-test the deployed system

Run these tests in order:

1. Open the Cloudflare Pages URL.
2. Confirm login works over HTTPS.
3. Confirm patient registration/login works.
4. Open Patients and search for a patient.
5. Open Clinical Review.
6. Test **Generate AI summary** and confirm the response shows provider/model/output.
7. Test **Run AI decision support** and confirm non-empty output.
8. Generate a report.
9. Add clinician recommendation/guidance.
10. Click **Review**.
11. Click **Approve & Send to Patient**.
12. Login as the corresponding patient and open **My Health**.
13. Confirm the released report appears and mark it reviewed.
14. Login as administrator and confirm reviewed/released report status is visible.
15. Confirm clinician report deletion works as expected.

## Step 10 — Check that you have not accidentally enabled paid services

GitHub: remain on Free.

Render: API service must show the Free compute plan. Do not add Render Postgres for this $0 architecture.

Neon: project must remain on Free.

Cloudflare Pages: use static Pages; do not add Workers/Functions unless you explicitly need them.

Gemini: stay on the free tier and do not attach paid billing for this deployment.

Also: **do not add a payment method to Render**. Render states that when a user has no payment method and would incur charges, it disables the affected services for the billing period rather than billing them.

## Data / healthcare warning

This deployment architecture is intended for a no-cost demonstration/test setup. Render explicitly says its Free instances are not for production applications. The application also handles health information. Before using real patient/clinical data, verify hosting/privacy terms, data residency, security controls, access control, logging, backups, AI-provider terms, and applicable healthcare/privacy obligations in your jurisdiction.

## Batch22 boundary

This package changes deployment plumbing only. It does not replace or rewrite the working CareSphere frontend/backend implementation. Apply it on top of the latest tested source tree.
