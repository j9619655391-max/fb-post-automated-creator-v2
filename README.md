# Content Automation Platform

Enterprise-grade content automation platform with manual approval workflows and comprehensive audit logging.

**Stack:** Python/FastAPI. Docs: [docs/README.md](docs/README.md) — ARCHITECTURE, PROJECT_STATUS_SUMMARY, ROADMAP_AND_PRODUCT, IMPLEMENTATION_AND_REMAINING_DETAIL, GIT_SYNC_GUIDE.

## Features

- **Content Management**: Create, update, and manage content with approval workflows
- **Approval Workflow**: Draft → Pending Approval → Approved/Rejected
- **Audit Logging**: Complete audit trail of all system actions
- **User Management**: Role-based access control (Admin/User)
- **Facebook OAuth (Phase 1)**: Single Meta App, user consent only; token encryption at rest; login/callback
- **Page tokens (Phase 2)**: Sync/list Facebook pages; page access tokens encrypted at rest
- **User-configurable posting (Phase 3)**: Schedule approved content to a page; scheduler executes only when user schedules; safety limits (cooldown, max/day); cron/run with secret
- **AI draft generation**: Generate a complete, approval-required draft with structured Gemini output and persisted provenance
- **Generation plans**: Daily/weekly recurring plans create approval-required AI drafts through Celery Beat
- **Meta compliance (Phase 4)**: App Review doc (docs/META_APP_REVIEW.md); FB API error handling; Posting Recommendation Engine (advisory API)
- **RESTful API**: Clean FastAPI-based REST API

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy (ORM)
- SQLite (database)
- Cryptography (token encryption), httpx (OAuth)
- Docker-ready

## Project Structure

```
app/
├── api/              # API routes
│   └── routes/       # Route handlers (content, users, audit_logs, auth_facebook)
├── core/             # Core configuration
│   ├── config.py     # Settings (incl. Meta OAuth env)
│   ├── database.py   # DB connection
│   └── token_crypto.py  # Token encryption at rest
├── models/           # SQLAlchemy models (incl. meta_oauth)
├── schemas/          # Pydantic schemas
├── services/         # Business logic (facebook_oauth, facebook_pages)
└── main.py           # FastAPI app
```

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Run the UI (optional):**
   ```bash
   cd frontend && npm install && npm run dev
   ```
   - UI: http://localhost:5173 (proxies API to http://localhost:8000)
   - Sign in with **User ID** (e.g. `1` for admin). Seed DB first: `python scripts/init_db.py`

4. **Access the API directly:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **Run tests:**
   ```bash
   pytest tests/ -v
   ```
   Tests use in-memory SQLite (no `.db` file). Requires `httpx<0.28` (see requirements.txt).

### Local provider sandbox

For PostgreSQL, Redis, Celery, OAuth callbacks, and safe Meta/Instagram/LinkedIn sandbox validation, follow [docs/LOCAL_PROVIDER_SANDBOX_RUNBOOK.md](docs/LOCAL_PROVIDER_SANDBOX_RUNBOOK.md). The provider readiness command is safe and performs no network calls:

```bash
python scripts/provider_readiness.py
```

The optional `docker-compose.local.yml` starts only PostgreSQL and Redis; run FastAPI, Celery Worker, Celery Beat, and the frontend in separate terminals as described in the runbook.

### Docker

1. **Build and run (image includes API + built frontend):**
   ```bash
   docker-compose up --build
   ```
   The Dockerfile uses a multi-stage build: Node builds the frontend, then the Python image copies `frontend/dist` and runs `python -m scripts.init_db` (tables + seed) before starting the API. The app serves the UI at `/`.

2. **Restart with Docker** (after code or env changes):
   ```bash
   docker-compose down
   docker-compose up --build
   ```
   This rebuilds the image (including frontend) and recreates the container. Ensure `.env` has `GEMINI_API_KEY` (optional) and `DATABASE_URL` is unchanged if you keep `./data` for the DB.

3. **Access the app:**
   - **UI:** http://localhost:8000 (sign in with User ID; seed creates admin + user1)
   - **API:** http://localhost:8000/api/v1
   - **Docs:** http://localhost:8000/docs

4. **Optional env:** Set `GEMINI_API_KEY` in `.env` for AI theme generation on the "New content" page (category → themes). Set Facebook OAuth vars for login/sync/publish.

## API Endpoints

### Content
- `POST /api/v1/content/` - Create content
- `GET /api/v1/content/` - List content
- `GET /api/v1/content/{id}` - Get content
- `PATCH /api/v1/content/{id}` - Update content (draft only)
- `POST /api/v1/content/{id}/submit` - Submit for approval
- `POST /api/v1/content/{id}/approve` - Approve/reject (admin only)
- `POST /api/v1/content/{id}/publish-to-facebook` - Publish content to a Facebook Page (body: `meta_page_id`); sets `fb_page_id`, `fb_post_id`, `fb_status`
- `DELETE /api/v1/content/{id}` - Delete content (draft only)

### Users
- `POST /api/v1/users/` - Create user (admin only)
- `GET /api/v1/users/` - List users (admin only)
- `GET /api/v1/users/me` - Get current user

### Audit Logs
- `GET /api/v1/audit-logs/` - List audit logs (admin only)
- `GET /api/v1/audit-logs/{id}` - Get audit log (admin only)

### Auth (Facebook OAuth)
- `GET /api/v1/auth/facebook/login` - Redirect to Facebook consent (requires `user_id` query for MVP)
- `GET /api/v1/auth/facebook/callback` - OAuth callback; redirects to `/?facebook=connected`
- `POST /api/v1/auth/facebook/disconnect` - Disconnect Facebook (remove token and pages; user must re-auth and sync)

### Meta / Pages
- `GET /api/v1/meta/pages/` - List connected Facebook pages (no tokens in response)
- `POST /api/v1/meta/pages/sync` - Sync pages from Meta (/me/accounts); stores encrypted page tokens
- `GET /api/v1/meta/pages/{id}/recommendations` - Advisory posting recommendations (time windows, category×time, frequency); user decides

### Scheduled posts
- `POST /api/v1/scheduled-posts/` - Schedule approved content to a page (content_id, meta_page_id, scheduled_at)
- `GET /api/v1/scheduled-posts/` - List scheduled posts (filters: status, meta_page_id)
- `GET /api/v1/scheduled-posts/{id}` - Get scheduled post
- `PATCH /api/v1/scheduled-posts/{id}/cancel` - Cancel PENDING scheduled post
- `GET /api/v1/scheduled-posts/preferences/{meta_page_id}` - Get posting preference (cooldown, max/day)
- `PUT /api/v1/scheduled-posts/preferences/{meta_page_id}` - Set posting preference

### Cron (server-side only)
- `POST /api/v1/cron/run?secret=CRON_SECRET` - Process due scheduled posts; call from cron job

### AI generation and automation plans
- `POST /api/v1/generation/draft` - Generate and persist one complete AI draft; approval is still required
- `POST /api/v1/generation-plans/` - Create a daily/weekly approval-required generation plan
- `GET /api/v1/generation-plans/` - List accessible generation plans
- `POST /api/v1/generation-plans/{id}/pause` - Pause a plan
- `POST /api/v1/generation-plans/{id}/resume` - Resume a plan
- `POST /api/v1/generation-plans/{id}/run-now` - Generate one draft immediately from an active plan

### Viral Content Engine (VCE – advisory)
- `GET /api/v1/vce/categories` - List content categories
- `GET /api/v1/vce/categories/today` - Today's suggested category (rotation)
- `GET /api/v1/vce/templates` - List hook templates (placeholders: {hook}, {body}, {cta})
- `GET /api/v1/vce/suggested-template` - Suggested template for today (by category rotation)
- `GET /api/v1/vce/generate-themes` - Generate content themes via Gemini (query: `category_id`, `category_name`, `count`; requires `GEMINI_API_KEY`)
- `GET /api/v1/vce/share-psychology-tips` - Advisory share-psychology tips

## Content Workflow

1. **Draft**: Content is created in draft status
2. **Pending Approval**: Content is submitted for approval
3. **Approved/Rejected**: Admin approves or rejects the content

Only draft content can be updated or deleted.

## Authentication

**Current:**
- **API:** Username/email + password login returns a JWT bearer token. Protected endpoints require `Authorization: Bearer <token>`.
- **Facebook OAuth:** Single Meta App; user consent only. Tokens encrypted at rest. No user App ID/Secret.
- **Automation safety:** Generated drafts are approval-required by default; scheduled publishing only executes approved content.

For local development, create an account with `POST /api/v1/auth/signup`, log in with `POST /api/v1/auth/login`, and send the returned bearer token on protected requests.

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`: Database connection string
- `DEBUG`: Enable debug mode
- `API_PREFIX`: API route prefix
- **Facebook OAuth (optional):** `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_REDIRECT_URI`, `TOKEN_ENCRYPTION_KEY` (e.g. from `Fernet.generate_key().decode()`)
- **LinkedIn OAuth (optional):** `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI`
- **Cron (optional):** `CRON_SECRET` — secret for `POST /api/v1/cron/run` (server-side only)
- **Gemini (optional):** `GEMINI_API_KEY` — for AI theme generation on New content (GET /vce/generate-themes)
- **Celery (optional):** `CELERY_BROKER_URL` — Redis URL for scheduled Facebook posts (default `redis://localhost:6379/0`). Run Redis and: `celery -A app.scheduler worker -l info`

## Running the scheduler (Celery + Redis)

To run scheduled Facebook posts at the chosen time:

1. Start Redis: `redis-server`
2. Start the Celery worker: `celery -A app.scheduler worker -l info`
3. Create content with "Schedule for" + page on the New content form (or use POST /api/v1/scheduled-posts/). When content is approved, the task runs at the scheduled time.

## Database

SQLite database is created automatically on first run (or by `python -m scripts.init_db` in Docker). Tables: `users`, `content`, `audit_logs`, `oauth_states`, `meta_user_tokens`, `meta_pages`, `scheduled_posts`, `posting_preferences`, `content_categories`, `hook_templates`. Content has optional Facebook fields: `fb_page_id`, `fb_post_id`, `fb_status`; and optional schedule intent: `schedule_at`, `schedule_meta_page_id` (used when content is approved to create a Celery scheduled post). With Docker, DB path is `/app/data/content_platform.db` (host `./data`). For an existing DB, add new columns if needed (see docs) or remove `./data` and restart to recreate.

## Project Status

✅ **Core + Phases 1–4** (February 2025)

- Core: content, approval, audit, users, API
- Phase 1: Facebook OAuth (single Meta App; token encryption at rest)
- Phase 2: Page tokens (sync/list pages; encrypted at rest)
- Phase 3: Scheduled posts, posting preferences, post to Page (Graph API), cron/run
- Phase 4: Meta App Review doc, FB API error handling, Posting Recommendation Engine (advisory)
- Phase 5: Long-lived user token (~60d), audit for OAuth/pages/scheduled posts, list_content filter by user when not admin
- Phase 6: Token expiry/re-auth (clear token on invalid/expired; POST /auth/facebook/disconnect)
- Phase 7: Viral Content Engine — category rotation, hook templates (GET /vce/...); all advisory
- Phase 8: Share-psychology (GET /vce/share-psychology-tips); pytest suite in `tests/` (run: `pytest tests/`)
- **UI:** React app in `frontend/` (Vite, TypeScript, Tailwind): Dashboard, Content CRUD, submit/approve/reject, **Publish to Facebook** (content detail: select page, publish), **New content with AI** (category → generate themes → load into form), Audit logs, Users (admin). Run: `cd frontend && npm run dev`. When `frontend/dist` exists, FastAPI serves the SPA at `/`.
- **Facebook Graph:** `app/services/fb_api.py` — `publish_to_facebook()`; rate limit and invalid-token handling. Content model: `fb_page_id`, `fb_post_id`, `fb_status`.
- **VCE + Gemini:** GET `/vce/generate-themes`; theme generation service uses `GEMINI_API_KEY`.
- See `docs/IMPLEMENTATION_AND_REMAINING_DETAIL.txt` and `docs/META_APP_REVIEW.md`

## Documentation

See [docs/README.md](docs/README.md) for the full index. Core docs:

- `docs/ARCHITECTURE.md` - Architecture specification
- `docs/PROJECT_STATUS_SUMMARY.md` - Status and pending work
- `docs/ROADMAP_AND_PRODUCT.md` - Roadmap, MVP, Meta, VCE
- `docs/IMPLEMENTATION_AND_REMAINING_DETAIL.txt` - Implemented vs remaining (detail)
- `docs/META_APP_REVIEW.md` - Meta App Review (permissions, token handling)
- `docs/GIT_SYNC_GUIDE.md` - Git sync and ignore rules

## License

MIT



## OpenRouter free-model support

The AI provider layer supports both Gemini and OpenRouter. Gemini remains the default in `.env.example`; to use OpenRouter’s free router locally, set the server-side environment values below and recreate the API container:

```dotenv
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your-server-side-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/free
OPENROUTER_TIMEOUT_SECONDS=60
OPENROUTER_INPUT_COST_PER_MILLION_USD=0.0
OPENROUTER_OUTPUT_COST_PER_MILLION_USD=0.0
AI_FALLBACK_ENABLED=false
```

`openrouter/free` selects an available free model dynamically. A specific free model can be selected by setting `OPENROUTER_MODEL` to a currently available model slug ending in `:free`; availability changes over time, so operators should verify the live OpenRouter model catalog before pinning one. The provider adapter records prompt, completion, and total tokens in the existing usage table and uses the configured rates for cost accounting. Free-model defaults are recorded at zero cost, but operators should review provider pricing before changing model configuration.

An optional Gemini fallback exists but is disabled by default because it may incur cost. Set `AI_FALLBACK_ENABLED=true` only when that behavior is explicitly desired. Provider keys remain server-side, are never sent to the frontend, and are not included in Git commits. AI-generated content remains a draft until it passes the existing moderation and human approval workflow.
