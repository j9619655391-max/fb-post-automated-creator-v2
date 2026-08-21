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


## Production-readiness checkpoint: PostgreSQL, LinkedIn scheduling, and AI quotas

The provider-neutral scheduled target migration was validated against PostgreSQL 16. During validation, the migration exposed and fixed a PostgreSQL-specific issue: the `scheduledplatform` enum type is now explicitly created before the target column is added and safely reused by subsequent content scheduling fields. `alembic upgrade head` and `alembic check` now pass against the staging database.

Redis 7 and a real Celery worker were started locally. The worker successfully registered `publish_scheduled_post_task`, `run_due_generation_plans_task`, and `token_guard_task`; `celery inspect ping` returned `pong`; and a database-backed `token_guard_task` was enqueued and completed successfully through Redis with PostgreSQL as the worker database.

Inline scheduling now supports Facebook, Instagram, and LinkedIn end to end. Content creation stores a provider-neutral schedule platform plus either a Meta page or LinkedIn account target. Approval validates future timestamps, target ownership through the scheduler, and mutually exclusive targets before enqueueing the unified scheduled-post executor. The frontend ContentForm now loads LinkedIn accounts and exposes a platform/target selector.

Organization-scoped monthly AI quotas were added for request count and total tokens, with tier defaults and database setting overrides. Generation rejects new work with HTTP 429 after the limit is reached, while idempotent requests remain safe. Billing usage now includes current-month utilization, configured limits, and remaining request/token allowances. The scheduled executor also emits structured lifecycle logs for processing, success, retries, terminal failures, and dead-letter transitions.

## Validation

| Check | Result |
|---|---:|
| PostgreSQL 16 connectivity | Passed |
| Alembic PostgreSQL upgrade | Passed |
| Alembic PostgreSQL drift check | Passed |
| Redis connectivity | Passed |
| Celery worker ping | Passed |
| Real Redis-backed Celery task | Passed |
| Python compilation | Passed |
| Backend tests | **23 passed** |
| Frontend `npm run build` | Passed |
| Inline LinkedIn scheduling test | Passed |
| AI quota enforcement test | Passed |

## Remaining production boundary

Actual Meta Graph and LinkedIn sandbox publishing still requires configured provider credentials, approved callback URLs, and real test accounts. Production deployment should also add external metrics and alert routing, moderation and duplicate-content gates, CI/CD migration checks, and cleanup of existing Pydantic/SQLAlchemy deprecation warnings.


## Additional hardening checkpoint: moderation, recovery diagnostics, and CI

A deterministic moderation layer now runs after AI response validation and before an AI draft is persisted as content. It blocks a narrowly defined set of clearly dangerous instructions, illegal-drug trade language, self-harm encouragement, and deceptive financial claims. AI-provided risk flags remain attached to the generation job for human review. Organization-scoped exact duplicate detection also prevents repeated title/body pairs from entering the approval queue.

Scheduled-post API responses now expose provider labels, retryability, recovery actions, and user-facing recovery hints derived from stable failure codes. The dashboard uses these fields to distinguish re-authentication, retry, policy-review, and generic review actions.

A GitHub Actions workflow was added to run Python compilation, the complete backend test suite, PostgreSQL Alembic upgrade/drift validation, and the frontend production build on pushes and pull requests to `main`. Application-side Pydantic v2 configuration warnings and the content approval UTC timestamp warning were cleaned up without changing the approval-required publishing default.

## Validation

| Check | Result |
|---|---:|
| Backend tests | **26 passed** |
| Python compilation | Passed |
| Frontend `npm run build` | Passed |
| Moderation and duplicate detection tests | Passed |
| Recovery metadata serialization | Passed |
| Git diff whitespace check | Passed |
| Application-side Pydantic config warnings | Cleaned |

## Remaining boundary

The deterministic moderation layer is intentionally conservative and explainable; it does not replace provider policy enforcement, media scanning, brand-specific rules, or human approval. Real provider sandbox publishing and production infrastructure validation still require configured Meta/Instagram/LinkedIn credentials and deployment endpoints.


## Provider sandbox readiness checkpoint

A safe provider-readiness diagnostic now validates Meta, Instagram/Meta, LinkedIn, Gemini, database, Celery broker, encryption, production secret, debug mode, and OAuth callback configuration without making any external API calls or printing secret values. Strict mode is available for deployment gates and correctly reports missing local provider credentials until they are supplied.

The local sandbox workflow is documented in `docs/LOCAL_PROVIDER_SANDBOX_RUNBOOK.md`. It covers PostgreSQL, Redis, FastAPI, Celery Worker, Celery Beat, frontend startup, OAuth callback tunneling, approval-required rollout, provider-specific prerequisites, and teardown. `docker-compose.local.yml` provides a reproducible PostgreSQL 16 and Redis 7 data layer. `.env.example` now includes LinkedIn OAuth variables and exact local callback paths, and the README links to the runbook.

## Validation

| Check | Result |
|---|---:|
| Provider readiness diagnostic | Passed; no network calls made |
| Strict readiness missing-credential behavior | Passed |
| Backend tests | **26 passed** |
| Python compilation | Passed |
| Frontend build | Passed |
| PostgreSQL Alembic drift check | Passed |
| Git whitespace check | Passed |

## Remaining provider gate

Actual E2E publishing remains intentionally gated on user-supplied Meta and LinkedIn developer credentials, connected test targets, and callback URLs. Until then, local and mocked validation remains the safe execution mode.


## Windows local integration checkpoint

The Windows Docker deployment was corrected and revalidated. The API image now includes Alembic configuration and migrations, only the API runs startup migrations, the API seeds missing default content categories/templates idempotently, and API/Celery/Beat reuse one local application image. Windows lifecycle scripts (`start-local.bat`, `status-local.bat`, and `stop-local.bat`) were added.

The browser-console integration issues were mapped and addressed. Workspace list/create/member flows pass locally. Missing Gemini configuration now returns an explicit provider configuration response instead of a generic generation failure. Platform status exposes provider readiness, and the frontend prevents predictable Facebook/LinkedIn OAuth 503 calls when credentials are absent, showing setup guidance instead.

| Local check | Result |
|---|---:|
| API root and docs | Passed |
| Signup/login/authenticated user smoke | Passed |
| Organization list/create/member smoke | Passed |
| Missing Gemini generation gate | Passed; returns 503 with setup guidance |
| PostgreSQL Alembic drift | Passed |
| Celery worker ping | Passed |
| Celery Beat startup | Passed |
| Frontend production build | Passed |


## Workspace intelligence and source-aware generation checkpoint

Workspace business intelligence is now organization-scoped and permissioned. Owners, administrators, and editors can maintain the structured profile and source records; ordinary members can read intelligence but cannot modify it. The API supports profile upsert/retrieval, source creation, source refresh, bulk refresh, and soft deletion. Personal/private data collection is not part of the ingestion workflow; the feature is designed for authorized public business information and official API data.

Website source ingestion includes SSRF protections for schemes, credentials, localhost, private/reserved/link-local/multicast addresses, robots.txt handling, HTML-only extraction, response and text limits, safe redirect validation, and sanitized text extraction with BeautifulSoup. Refreshes deliberately downgrade content to `pending` review and `user_supplied` trust until a human reviews the newly fetched material.

Generation context is restricted to the active approved source set and the organization profile. Prompt instructions identify source excerpts as untrusted reference data, prevent embedded source commands from being followed, require supported claims, and capture source type/title/URL/trust-level hints in the content-generation audit record for human review. This context does not change the approval-required publishing default or bypass moderation, duplication, quota, or provider failure controls.

| Check | Result |
|---|---:|
| Workspace intelligence endpoint tests | **5 passed** |
| Full backend suite | **31 passed** |
| Python compilation | Passed |
| Frontend `npm run build` | Passed |
| PostgreSQL workspace migration upgrade | Passed |
| PostgreSQL `alembic check` | Passed; no new upgrade operations |
| Docker API health endpoint | Passed; HTTP 200 |
| Docker root/frontend response | Passed; HTTP 200 |

## Remaining production boundary

The feature is ready for local controlled use, but automatic source refresh and actual publishing still require configured provider credentials, approved HTTPS callbacks, authorized business accounts, and operational monitoring. External provider sandbox E2E tests, alerting/metrics, and any future autonomous campaign mode remain gated behind the existing human-approval and credential requirements.


## OpenRouter free-model hardening checkpoint

OpenRouter is integrated as an optional server-side AI provider through the existing generation client abstraction. The adapter uses the documented HTTPS endpoint and Bearer authentication, handles non-JSON/provider/network errors without exposing API keys, captures the resolved model returned by the provider, and normalizes token usage into the existing billing table. The default `openrouter/free` router selects from currently available free models; specific free variants can be pinned with a `:free` model slug.

OpenRouter fallback to Gemini is explicitly disabled by default because it may create paid-provider cost. Operators must set `AI_FALLBACK_ENABLED=true` deliberately. The dashboard provider card and authenticated provider-status endpoint expose provider, model, configuration readiness, free-model status, and fallback state only; no secret is serialized to the browser or audit response.

| Check | Result |
|---|---:|
| OpenRouter model catalog probe | Passed; HTTP 200 |
| OpenRouter free completion probe | Passed; HTTP 200 and zero provider cost reported |
| Draft-only OpenRouter API smoke test | Passed; approval-required draft created |
| Backend suite | **36 passed** |
| Provider adapter tests | Passed |
| Python compilation | Passed |
| Frontend production build | Passed |
| PostgreSQL Alembic drift check | Passed |
| Docker API/Worker/Beat deployment | Healthy |

## Remaining provider boundary

OpenRouter free-model availability and rate limits can change, and free models may have higher latency or weaker structured-output reliability than paid models. Production operation should pin and periodically verify an appropriate `:free` model when deterministic behavior is required, monitor provider failures, and rotate the credentials supplied during setup because they were shared in chat. Meta/Facebook, Instagram, and LinkedIn publishing remains governed by the existing provider credentials, OAuth callbacks, moderation, and human approval controls.


## Production-readiness checkpoint: AI provider resilience

OpenRouter provider failures now carry sanitized HTTP status, retryability, and integer `Retry-After` metadata. The generation service maps these errors to `GenerationProviderError` without leaking credentials. `run_due_plans()` applies a bounded five-minute-to-one-hour retry window for retryable provider failures and advances non-retryable failures to the next daily/weekly occurrence, preventing repeated hot-loop execution.

Recurring generation plans persist the last provider, error code/message, failure count, and retry timestamp. Migration `e5f6a7b8c9d0` is applied and `alembic check` reports no drift. The background OpenRouter smoke test generated an approval-required draft through the real Celery task path; the publishing executor was not invoked.

| Validation | Result |
|---|---:|
| Complete backend suite | **37 passed** |
| Generation-plan/OpenRouter focused suite | **7 passed** |
| Python compileall | Passed |
| Frontend production build | Passed |
| Alembic upgrade and drift check | Passed |
| API root smoke check | HTTP 200 |
| PostgreSQL and Redis health | Healthy |
| API, Celery Worker, Celery Beat | Running |
| Real social publishing during validation | Not attempted |

Credential rotation remains a required operator action because the original keys were shared in chat. Replace both provider keys in the local ignored `.env`, recreate API/Worker/Beat, and rerun the provider smoke test after rotation.


## Production-readiness checkpoint: provider health and sandbox controls

The readiness diagnostic now treats the configured AI provider as the required AI check and treats the other provider key as optional. It never calls Meta, Instagram, LinkedIn, Gemini, or OpenRouter and never prints secret values. An authenticated provider-health endpoint reports only provider/model configuration, recent failed generation counts, retrying-plan counts, alert state, and sanitized latest error metadata.

A 15-minute Celery health task performs the same local-only inspection and logs a sanitized alert event when configuration is missing or failure thresholds are exceeded. The running worker was recreated and confirmed to register `app.ai_provider_health_task` alongside generation and publishing tasks. The dashboard displays an alert indicator but does not expose provider credentials.

The current sandbox audit confirms that Meta and LinkedIn credentials, secure callbacks, token encryption, and a non-default production secret are still required before live publishing tests. Meta Pages publishing requires the appropriate Page permissions and tasks; Instagram requires a professional account, connected authorization, publicly accessible media, and application-side rate-limit enforcement; LinkedIn organization publishing requires the appropriate organization permission and member role. These findings are documented with official references in `docs/PROVIDER_SANDBOX_READINESS_FINDINGS.md`.

Validation: **39 backend tests passed**, Python compilation passed, frontend build passed, Alembic reported no drift, API returned HTTP 200, PostgreSQL and Redis were healthy, and no public social post was created.


## Production-readiness checkpoint: sandbox validation controls

The platform now exposes a read-only sandbox-readiness check for Facebook, Instagram, and LinkedIn. It performs no publishing, does not return access tokens, and sanitizes provider errors into configuration, permission, rate-limit, or availability messages. Meta validation uses only account/page discovery; LinkedIn validation uses only member identity; Instagram remains blocked until professional-account linkage is modeled and verified.

The authenticated live route returned `401` without credentials, confirming the route is protected. The full regression suite passed with **41 tests**. Python compilation, frontend build, Alembic drift validation, and Docker runtime checks passed. No external social publishing was attempted.
