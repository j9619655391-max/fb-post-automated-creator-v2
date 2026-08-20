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
