# Local Provider Sandbox Runbook

This runbook starts the Facebook, Instagram, and LinkedIn auto-post platform locally while preserving the project’s **approval-required default**. It separates safe local validation from real provider calls and never places secrets in source control.

## 1. Prepare local configuration

From the repository root, copy the example environment file and edit only the local `.env` file:

```bash
cp .env.example .env
```

Generate a token encryption key and place the output in `TOKEN_ENCRYPTION_KEY`:

```bash
python -m scripts.generate_encryption_key
```

For local OAuth, use these callback URLs in the Meta Developer Console and LinkedIn Developer Portal:

```text
http://localhost:8000/api/v1/auth/facebook/callback
http://localhost:8000/api/v1/auth/linkedin/callback
```

When the provider requires HTTPS or cannot reach localhost, run an HTTPS tunnel to port `8000` and set both redirect URI settings to the tunnel URL with the same callback paths. The callback URL configured in the provider console must match `FACEBOOK_REDIRECT_URI` or `LINKEDIN_REDIRECT_URI` exactly.

## 2. Start PostgreSQL and Redis

A Docker-based local data layer is available in `docker-compose.local.yml`:

```bash
docker compose -f docker-compose.local.yml up -d
```

If Docker is unavailable, use the native services already installed on Linux:

```bash
sudo -u postgres pg_ctlcluster 16 main start
redis-server --daemonize yes
```

Set the local database and broker values in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://fb_post:local_staging_password@localhost:5432/fb_post_local
CELERY_BROKER_URL=redis://localhost:6379/0
```

Create the database and role once when using native PostgreSQL:

```bash
sudo -u postgres psql -c "CREATE USER fb_post WITH PASSWORD 'local_staging_password';"
sudo -u postgres psql -c "CREATE DATABASE fb_post_local OWNER fb_post;"
```

## 3. Apply migrations and run readiness checks

```bash
alembic upgrade head
alembic check
python scripts/provider_readiness.py
```

Use strict mode only after provider credentials, callbacks, encryption, and production-safe secrets have been configured:

```bash
python scripts/provider_readiness.py --strict
```

The readiness diagnostic never calls Meta, Instagram, LinkedIn, or Gemini and never prints secret values.

## 4. Start the application processes

Use separate terminals from the repository root:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
celery -A app.scheduler worker -l info
```

```bash
celery -A app.scheduler beat -l info
```

```bash
cd frontend
npm ci
npm run dev
```

The API is available at `http://localhost:8000`, the frontend at `http://localhost:5173`, and the API documentation at `http://localhost:8000/docs`.

## 5. Safe validation order

First validate signup/login, content generation, moderation rejection, duplicate detection, approval, target selection, quota rejection, and scheduled-post state transitions using local or mocked providers. Then connect one Meta test Page, one Instagram Business account, or one LinkedIn test account at a time.

Use the authenticated `POST /api/v1/auth/facebook/login` or `POST /api/v1/auth/linkedin/login` endpoint to begin OAuth. The application creates a short-lived, one-time server-side state; do not append JWTs or access tokens to callback URLs.

Keep the first real publish test as a manually approved single post. Verify the resulting provider post ID, local `POSTED` status, audit record, and dashboard recovery behavior before testing retries or scheduled execution.

## 6. Provider-specific prerequisites

| Provider | Required local setup | First safe test |
|---|---|---|
| Facebook | Meta app credentials, Page access, exact callback URL, and encrypted token storage | Approve and publish one text post to a test Page |
| Instagram | Instagram Business/Creator account connected to a Facebook Page and a publicly reachable image URL | Approve and publish one image post |
| LinkedIn | LinkedIn app credentials, approved product scopes, and a connected profile/company target | Approve and publish one short text post |

Provider API calls remain disabled until the corresponding credentials and connected test target are supplied. Do not use personal production pages or accounts for the first test.

## 7. Stop and reset

Stop the local API, worker, and Beat processes with `Ctrl+C`. Stop the Docker data layer with:

```bash
docker compose -f docker-compose.local.yml down
```

For native services, stop only the local staging services when they are no longer needed:

```bash
sudo -u postgres pg_ctlcluster 16 main stop
redis-cli shutdown
```

Never commit `.env`, provider access tokens, OAuth client secrets, or generated encryption keys.
