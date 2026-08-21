# Automation Implementation Progress

**Baseline:** `main` at `9b7156d`  
**Current scope:** Foundation stabilization, complete AI draft generation, recurring approval-required generation plans, and publishing-state hardening.

## Completed in this implementation pass

| Area | Completed work |
|---|---|
| AI runtime | Fixed Gemini client initialization in `AIService`; added deterministic provider-mocked test |
| Authentication tests | Replaced stale query-parameter fixtures with JWT signup/login fixtures |
| Dependency stability | Pinned `bcrypt==4.0.1` for compatibility with `passlib==1.7.4` |
| Content authorization | Added creator/organization membership checks to content mutations and organization-filtered listing |
| Scheduling validation | Rejected past schedule times and inconsistent approval schedule intent |
| Queue idempotency | Added deterministic scheduled-post idempotency keys and duplicate protection |
| Worker truthfulness | Parent scheduled jobs no longer become `POSTED` when target publishing failed |
| Worker states | Added retrying, partial-failure, dead-letter, attempt, retry-time, and completion metadata |
| AI complete drafts | Added structured Gemini JSON generation, validation, persisted `ContentGenerationJob`, and AI provenance on drafts |
| Generation API | Added `POST /api/v1/generation/draft` |
| Generation plans | Added daily/weekly recurring generation plans with active/paused state and run-now support |
| Background generation | Added Celery Beat task to process due plans; generated content remains approval-required |
| Frontend | Added complete-draft action, automation-plan screen, plan APIs, truthful calendar queue, and new worker-state labels |
| Documentation | Updated README authentication and automation endpoint documentation |
| Runtime fixes | Added missing `os` import to settings service and extended SQLite compatibility migrations |

## Validation completed

- `python3 -m compileall -q app scripts` — passed.
- `pytest tests/ -q` — **13 passed**.
- `npm run build` — passed.
- Frontend and backend changes compile successfully.

## Current automation behavior

The implemented generation plan creates a complete AI-generated `DRAFT` at the scheduled time. The draft carries generation provenance and must still pass the existing submit/approve workflow. Automatic publishing remains separate and only applies to approved, queued content.

## Remaining before controlled autopilot

1. Replace the deprecated `google.generativeai` SDK with the supported Gemini client.
2. Add a full worker integration test for target success, target failure, retry, and dead-letter transitions.
3. Add strict content/page ownership checks to every read, insight, and publishing route.
4. Apply cooldown and max-per-day safety policies inside the canonical Celery executor.
5. Add PostgreSQL/Alembic migrations for production deployment instead of relying on SQLite `create_all()` and compatibility ALTER statements.
6. Add generation usage/cost accounting and organization quotas.
7. Add moderation, duplicate-content detection, brand-voice policy validation, and media policy checks.
8. Replace JWT query-string transport in Facebook/LinkedIn OAuth with a one-time server-side initiation code.
9. Add rate limiting, private media URLs, secret validation, and production-safe bootstrap behavior.
10. Roll out in dry-run, approval-required, limited-pilot, and only then controlled-autopilot modes.


## Latest production-readiness checkpoint

The application now has provider-neutral inline scheduling across Facebook, Instagram, and LinkedIn. Content creation accepts a platform and target account, approval validates the schedule and dispatches the unified scheduled-post Celery executor, and the ContentForm includes a LinkedIn account selector alongside Meta targets. A PostgreSQL-specific Alembic enum issue was fixed and validated against PostgreSQL 16 with no migration drift.

Redis-backed Celery staging validation is complete: the worker registered all scheduled tasks, responded to an inspection ping, and successfully executed a database-backed token-guard task using PostgreSQL. Organization-scoped monthly AI request and token quotas are enforced before provider calls, exposed in billing usage responses, and visible in the billing UI. Scheduled publishing now emits structured lifecycle logs for operational troubleshooting.

The project currently validates with **23 backend tests passing**, Python compilation passing, frontend production build passing, PostgreSQL `alembic upgrade head` passing, and PostgreSQL `alembic check` reporting no drift.

Actual external Meta/Instagram and LinkedIn sandbox publishing remains deployment-dependent because it requires real provider credentials, callback URLs, and connected test accounts. Moderation, external metrics/alerting, CI/CD, and deprecation-warning cleanup remain follow-up production hardening items.


## Additional local hardening checkpoint

The AI draft pipeline now includes deterministic moderation and exact duplicate detection before generated content enters the approval workflow. Clearly dangerous instructions, illegal-drug trade language, self-harm encouragement, and deceptive financial claims are blocked with validation feedback; AI risk flags remain available for human review.

Scheduled-post responses now include provider labels, retryability, recovery action, and recovery hints. The dashboard uses those fields for clearer re-authentication, retry, policy-review, and generic-review actions. A GitHub Actions workflow now validates Python compilation, backend tests, PostgreSQL migrations, and the frontend build on changes to `main`.

Application-side Pydantic v2 configuration warnings and the content approval UTC timestamp warning were cleaned up. The local validation suite currently reports **26 backend tests passed**, Python compilation passed, frontend build passed, and whitespace checks passed.


## Provider sandbox readiness checkpoint

The repository now includes a no-network provider-readiness diagnostic for Meta/Facebook, Instagram/Meta, LinkedIn, Gemini, encryption, database, Celery, secret, debug, and OAuth callback settings. A strict mode is available for deployment gates and reports missing credentials without exposing secret values.

A reproducible local runbook and `docker-compose.local.yml` were added for PostgreSQL 16, Redis 7, FastAPI, Celery Worker, Celery Beat, frontend startup, OAuth tunneling, safe approval-required sandbox tests, and teardown. LinkedIn OAuth variables and exact callback examples are now included in `.env.example` and the README.

Local validation remains green with **26 backend tests passed**, Python compilation passed, frontend build passed, PostgreSQL Alembic drift check passed, and whitespace checks passed. Real provider publishing remains gated on developer credentials and connected test accounts.


## Windows local integration checkpoint

The Windows Docker deployment now runs PostgreSQL 16, Redis 7, FastAPI, Celery Worker, Celery Beat, and the frontend through a shared local application image. Alembic configuration/migrations are included in the image, only the API applies startup migrations, and missing default content categories/templates are seeded idempotently. Windows lifecycle scripts were added for start, status, and stop operations.

Workspace list/create/member flows were verified locally. Missing Gemini configuration now produces an explicit provider-configuration response, while platform status exposes readiness and the frontend prevents predictable OAuth 503 requests when provider credentials are not configured.

Local checks passed for API root/docs, authenticated HTTP smoke, organization list/create/member flows, PostgreSQL Alembic drift, Celery worker ping, Celery Beat startup, and the frontend production build. Real AI generation remains disabled until `GEMINI_API_KEY` is added to the local `.env`.


## Workspace business intelligence checkpoint

Each organization now has a structured business intelligence profile for authorized public business context, including description, mission, industry, services, products, audience, locations, brand voice, preferred languages, official website and social URLs, WhatsApp Business details, public business contact details, approved claims, and prohibited claims. The profile is managed through the new `/api/v1/organizations/{org_id}/intelligence` API surface and the frontend KNOWLEDGE workspace screen.

Workspace sources support official or user-supplied website, Facebook, Instagram, LinkedIn, WhatsApp Business, and manually reviewed records. Website refreshes are restricted to public HTTP(S) destinations, reject credentials and private/reserved IP ranges, perform a robots.txt check, allow only HTML/XHTML extraction, strip non-content elements, cap response/text sizes, validate safe redirects, and reset refreshed content to `pending` review so a person must re-approve changed facts.

AI draft generation now loads the organization profile and only active, approved source excerpts. The Gemini prompt explicitly treats source text as reference data rather than instructions, rejects unsupported claims, and preserves source provenance hints in the generation audit metadata for human review. Approval-required publishing remains the default; workspace intelligence improves relevance but does not bypass moderation, duplicate detection, quotas, or approval gates.

A corrective Alembic migration removes the redundant profile organization index, and the local Compose file live-mounts application code, migrations, tests, and frontend output for Windows development. Validation completed with **31 backend tests passed**, Python compilation passed, frontend production build passed, PostgreSQL Alembic upgrade/check passed, and API/Docker health checks passed.

Remaining production work is unchanged: configure real Meta/Facebook, Instagram, LinkedIn, and Gemini credentials; validate provider sandbox publishing and OAuth callbacks over HTTPS; add external observability and alerting; and only then evaluate a controlled autonomous campaign flag while retaining human approval safeguards.


## OpenRouter free-model integration checkpoint

The AI provider layer now supports Gemini and OpenRouter through one provider-neutral interface. OpenRouter uses its OpenAI-compatible `/api/v1/chat/completions` endpoint, supports `openrouter/free` and specific `:free` model slugs, normalizes prompt/completion/total token usage, and records provider-specific estimated cost using configurable rates. Free-model defaults are configured at zero cost, while model pricing remains operator-configurable.

The local Windows deployment has been configured with the supplied credentials in the ignored server-side `.env` and is currently set to `AI_PROVIDER=openrouter` with `OPENROUTER_MODEL=openrouter/free`. A live provider probe returned HTTP 200 for the model catalog and completion endpoint, and a draft-only API smoke test generated an approval-required draft successfully. No public post was created or published.

An explicit `AI_FALLBACK_ENABLED` setting controls optional Gemini fallback and defaults to `false` so free-model failures cannot unexpectedly incur paid-provider cost. A safe authenticated `GET /api/v1/generation/provider` endpoint and dashboard card expose only provider/model/readiness metadata; credentials are never returned to the frontend. Full validation now reports **36 backend tests passed**, Python compilation passed, frontend production build passed, Alembic drift check passed, and the Docker API/worker/beat stack is healthy.


## Production-readiness checkpoint: background OpenRouter generation

Recurring generation plans were validated through the Celery task path with the active OpenRouter free router. A due plan generated one approval-required draft successfully, and no social post was published. Provider errors now preserve retryability and `Retry-After` metadata. Retryable OpenRouter failures are rescheduled with bounded backoff instead of remaining due every five-minute Beat cycle; non-retryable generation failures advance to the next recurrence.

Generation plans now persist `last_provider`, `last_error_code`, `last_error_message`, `failure_count`, and `last_retry_at`, and the API response exposes these fields for operator visibility. Migration `e5f6a7b8c9d0` was applied successfully. Final local validation passed: **37 backend tests**, Python compilation, frontend production build, Alembic drift check, API HTTP 200 smoke check, and healthy PostgreSQL/Redis/API/Celery/Celery Beat services.


## Production-readiness checkpoint: provider health and sandbox readiness

The provider readiness diagnostic now follows the active AI provider and reports Gemini/OpenRouter availability separately without printing secrets or making network calls. The current local audit reports the active OpenRouter provider configured, database and Celery configured, and debug mode disabled. Meta app credentials/callback, LinkedIn credentials/callback, token encryption, and non-default production `SECRET_KEY` remain intentionally unresolved until operator credentials and deployment values are supplied.

Added an authenticated `GET /api/v1/generation/health` endpoint and dashboard alert display for recent provider failures and generation-plan retries. Added the periodic `app.ai_provider_health_task` to Celery Beat at 15-minute intervals; it performs local database inspection only and logs sanitized alert metadata. The worker was reloaded and confirmed to register the health task. The full backend suite now passes with **39 tests**, along with Python compilation, frontend build, Alembic drift validation, API HTTP 200, and healthy Docker services.

Official sandbox prerequisites and links are recorded in `docs/PROVIDER_SANDBOX_READINESS_FINDINGS.md`. No external social publishing was attempted during this checkpoint.


## Production-readiness checkpoint: provider sandbox dry-run validation

Added an authenticated `GET /api/v1/platforms/sandbox-readiness` endpoint and Platforms UI card for non-publishing provider validation. When credentials are absent, it reports configuration gaps without making network calls. When an account is connected, it performs only safe read-only identity checks: Meta `/me/accounts` and LinkedIn `/v2/userinfo`. Instagram is explicitly reported as blocked until professional-account linkage and an Instagram account identifier are persisted; no publish endpoint is called.

The local route smoke test returned the expected unauthenticated `401`. The complete backend suite now passes with **41 tests**, Python compilation passed, frontend production build passed, Alembic reports no drift, and the local Docker stack remains operational. No Facebook, Instagram, or LinkedIn post was created.
