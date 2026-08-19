# Hardening Implementation Progress

## Completed in this checkpoint

The project now uses the official `google-genai` SDK through a shared client helper. Complete draft generation, theme generation, and AI optimization use `google.genai.Client` and `client.models.generate_content`. Provider response usage metadata is normalized into prompt, candidate, thought, cached, and total token counts. Each authenticated AI request creates a generation job and persists a related `content_generation_usage` row with configurable per-million-token rates and estimated USD cost.

The Celery publishing executor now evaluates Meta-page cooldown and daily post caps before calling the external publisher. It classifies failures into terminal authentication/permission/content errors and retryable rate-limit/network/provider errors. Retryable errors use bounded exponential backoff, while exhausted attempts become `DEAD_LETTER`; terminal auth and permission errors become `FAILED` without blind retries.

Alembic is now the schema authority. A baseline migration and OAuth hardening migration are present, application startup no longer calls `create_all()`, the seed script applies `alembic upgrade head` instead of manual `ALTER TABLE`, and container/API/worker/beat startup applies the migration head explicitly. The migration environment reads `DATABASE_URL` from application settings and supports PostgreSQL and SQLite batch operations.

Facebook and LinkedIn OAuth initiation no longer accepts JWTs in query parameters. Authenticated POST endpoints create short-lived, provider-bound, one-time server-side states and return the provider authorization URL. Callback validation checks provider, expiry, and consumption state. The frontend now starts OAuth through authenticated API requests.

## Validation

| Check | Result |
|---|---:|
| Python compilation | Passed |
| Backend tests | **17 passed** |
| Worker retry/dead-letter integration tests | Passed |
| OAuth state security tests | Passed |
| Alembic clean-database upgrade | Passed |
| Alembic drift check | Passed |
| Frontend `npm run build` | Passed |
| Legacy `google.generativeai` scan | No references |
| JWT OAuth query-token scan | No references |
| `git diff --check` | Passed |

## Known boundary

The existing scheduled-post schema has a Meta-page target and the Celery executor is named `publish_to_facebook_task`. This covers scheduled Facebook publishing and the shared Meta Graph path used by Instagram, with Meta-page cooldown and daily caps enforced before execution. The repository does not yet model a LinkedIn scheduled target in `ScheduledPost`; LinkedIn publishing remains a separate/manual publishing path. A subsequent migration should add a provider-neutral scheduled target model or nullable LinkedIn target relation before enabling recurring LinkedIn autopublishing under the same worker policy.

## Operational requirements

Before deployment, run `alembic upgrade head` against the target PostgreSQL database, set `GEMINI_API_KEY`, configure the model and pricing settings, start Redis/Celery/Celery Beat, and ensure Meta/LinkedIn callback URLs use the new authenticated initiation flow. The cost defaults are estimates and must be reviewed whenever Google pricing, model, or billing tier changes.
