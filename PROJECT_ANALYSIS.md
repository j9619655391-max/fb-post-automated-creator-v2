# FB Post Automated Creator — Complete Project Analysis

**Prepared by:** Manus AI  
**Repository:** `sahilk267/fb-post-automated-creator`  
**Analyzed checkout:** `main` at commit `9b7156d`  
**Analysis date:** 19 August 2026  

## Executive Summary

The repository is an **enterprise-oriented content operations platform**, not merely a small Facebook post generator. Its current implementation combines a FastAPI/SQLAlchemy backend, a React/Vite/Tailwind frontend, JWT/password authentication, organization workspaces, media storage, Facebook and Instagram publishing, LinkedIn OAuth and publishing, Gemini-assisted content creation, scheduled posting, Celery/Redis workers, Stripe billing, administrator settings, maintenance mode, quotas, and audit logging. The top-level README and older architecture documents describe an earlier Facebook-only MVP and are materially behind the code currently present.[README.md][1] [app/api/routes/__init__.py][2]

The core product flow is sound: an authenticated user creates draft content, optionally attaches media and scheduling intent, submits it for approval, an administrator approves or rejects it, and approved content can be published to one or more external destinations. Content-level approval state and per-destination publishing state are modeled separately, which is a stronger design than the legacy flat Facebook fields described in the older documentation.[app/models/content.py][3] [app/models/content_execution.py][4]

The principal risks are **documentation drift, insufficient automated test coverage, inconsistent runtime assumptions, and production-hardening gaps**. The current tests are stale relative to JWT authentication and fail five of seven tests in the checked environment. Python compilation and the frontend production build succeed, but the test suite does not represent the current application contract. The frontend dependency audit reports two high-severity runtime vulnerabilities in the selected React Router range, and the project still contains permissive or development-oriented defaults such as wildcard CORS, a default JWT secret, local SQLite, publicly exposed Redis in Compose, and demo credentials seeded by the container startup path.[app/core/config.py][5] [scripts/init_db.py][6] [docker-compose.yml][7]

> **Overall assessment:** The codebase has a broad and potentially valuable product foundation, but it should be treated as an actively evolving pre-production system rather than a verified enterprise-ready release. The next engineering priority should be to establish one authoritative architecture and authentication contract, repair the test suite around the current JWT/org/platform model, and harden secrets, authorization, worker idempotency, and deployment configuration before adding more features.

## 1. Repository Scope and Structure

The repository contains a Python backend under `app/`, a TypeScript React application under `frontend/`, operational scripts under `scripts/`, tests under `tests/`, and product/architecture documentation under `docs/`. The backend exposes 18 route modules and approximately 70 decorated route handlers across authentication, content, media, organizations, billing, administration, Facebook, LinkedIn, Instagram, scheduling, AI, and VCE capabilities.[app/api/routes/__init__.py][2]

| Area | Current implementation | Primary locations |
|---|---|---|
| API/runtime | FastAPI application, global exception handlers, CORS, health endpoint, optional SPA serving | `app/main.py` |
| Authentication | Password signup/login, bcrypt hashing through Passlib, stateless JWT bearer tokens | `app/api/routes/auth.py`, `app/api/dependencies.py`, `app/core/security.py` |
| Content | Draft, pending approval, approved/rejected workflow; CRUD and ownership/org checks | `app/models/content.py`, `app/services/content_service.py`, `app/api/routes/content.py` |
| Publishing | Facebook multi-page, LinkedIn multi-account, Instagram Business flow | `app/services/fb_api.py`, `app/services/linkedin_api.py`, `app/api/routes/instagram.py` |
| Integrations | Facebook OAuth/pages, LinkedIn OAuth/accounts, Gemini, Stripe, Google Drive | `app/services/`, `app/api/routes/` |
| Scheduling | Celery/Redis ETA tasks plus a separate cron-style due-post processor | `app/scheduler.py`, `app/services/scheduler_service.py`, `app/api/routes/cron.py` |
| Persistence | SQLAlchemy models; SQLite by default; PostgreSQL-oriented abstraction but no migration framework | `app/core/database.py`, `app/models/` |
| Media | Image/video upload with local filesystem or Google Drive backend | `app/api/routes/media.py`, `app/services/storage.py` |
| Frontend | Authenticated React Router app with dashboard, content editor, calendar, platforms, organizations, billing, insights, audit logs, and settings | `frontend/src/` |
| Deployment | Multi-stage Docker image; Compose API, Redis, Celery worker, and Celery Beat | `Dockerfile`, `docker-compose.yml` |

## 2. Actual Architecture and Data Flow

### 2.1 Request and application lifecycle

`app/main.py` creates the FastAPI application, initializes database tables in the lifespan hook, registers global exception handlers, mounts `/media`, and serves either a JSON root response or the compiled React SPA. The API router is mounted under the configurable `/api/v1` prefix. The application creates tables with `Base.metadata.create_all()` at startup, which is convenient for an MVP but is not a substitute for versioned migrations in a multi-instance production deployment.[app/main.py][8] [app/core/database.py][9]

Every API route included in the central router receives the `check_maintenance_mode` dependency. That dependency performs a database-backed settings lookup and blocks most API routes with HTTP 503 when maintenance mode is enabled, while allowing authentication and administrator-settings paths to remain available.[app/api/routes/__init__.py][2] [app/api/dependencies.py][10]

### 2.2 Authentication and authorization flow

The implemented authentication contract is JWT-based, not the `user_id` query-parameter model described by the README and older documentation. Signup creates a user with a bcrypt password hash; the first user in the database is automatically promoted to administrator. Login accepts either username or email, verifies the password, issues a bearer JWT containing the user ID as `sub`, and records a login audit event. Subsequent requests require `Authorization: Bearer <token>` through `OAuth2PasswordBearer`; the dependency decodes the JWT, loads the user, and checks `is_active`.[app/api/routes/auth.py][11] [app/api/dependencies.py][10] [app/core/security.py][12]

Logout is stateless: it returns success but does not revoke or invalidate the token. This is acceptable for a basic short-lived token model only if the security trade-off is explicit. The configured default lifetime is seven days, so a stolen token may remain usable for a substantial period unless the secret is rotated or the user is deactivated.[app/api/routes/auth.py][11] [app/core/config.py][5]

Authorization is implemented inconsistently across the codebase. Some routes use `current_user.is_admin`, some use organization membership roles, and the frontend organization context currently exposes `isAdmin = true` as a placeholder. The backend therefore contains the more meaningful authorization boundary, but this should be centralized into reusable policy dependencies and service-level ownership checks.[app/api/routes/content.py][13] [app/api/routes/admin_settings.py][14] [frontend/src/context/OrgContext.tsx][15]

### 2.3 Content and approval flow

The content lifecycle is represented by the `ContentStatus` enum: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, and `REJECTED`. Content is associated with its creator, optional approving user, optional organization, optional media, and optional scheduling intent. The service layer records audit entries in the same transaction for create, update, submit, approve/reject, and delete operations.[app/models/content.py][3] [app/services/content_service.py][16]

The effective flow is:

1. An authenticated user creates a draft.
2. The service verifies organization access when an organization ID is supplied.
3. The user may update or delete the draft, attach media, and set post-approval scheduling intent.
4. The user submits the draft for approval.
5. An administrator approves or rejects pending content.
6. If approved content contains scheduling intent, a scheduled-post record is created and a Celery ETA task is enqueued.
7. The content may also be published immediately to selected Facebook pages or LinkedIn accounts.

A notable authorization issue remains: `get_content()` returns any content by numeric ID without an explicit ownership or organization check in the route or service. Listing applies user filtering for non-administrators, but detail, update, submit, delete, insights, and publishing paths should be audited individually to ensure that a user cannot operate on another user’s content by guessing an ID.[app/api/routes/content.py][13] [app/services/content_service.py][16]

### 2.4 Per-destination publishing model

The current implementation uses `ContentPublishStatus` rows to record publishing independently for each Facebook page or LinkedIn account. Each execution can move through `PENDING`, `PROCESSING`, `POSTED`, or `FAILED`, with an external post ID and error message. The Facebook service verifies approval, iterates over requested page IDs, checks page ownership, posts text or media, and records per-page success or failure instead of failing the entire multi-page request.[app/models/content_execution.py][4] [app/services/fb_api.py][17]

This model is conceptually stronger than the legacy documentation, which refers to flat `fb_page_id`, `fb_post_id`, and `fb_status` fields. The documentation should be updated to make `ContentPublishStatus` the authoritative publishing model and to explain how platform-specific execution records relate to the parent content item.[README.md][1] [app/schemas/content.py][18]

### 2.5 Scheduling and worker flow

There are currently **two scheduling implementations**:

| Path | Trigger | Behavior | Main concern |
|---|---|---|---|
| Celery path | Approval with `schedule_at` and `schedule_meta_page_id` | Creates a `ScheduledPost`, enqueues an ETA task, retries failures, and marks the row posted/failed | Uses separate task state and can duplicate effects without idempotency safeguards |
| Cron path | `POST /api/v1/cron/run?secret=...` | Scans due pending rows, applies cooldown/max-per-day limits, posts synchronously, and writes audit events | Does not appear to be the path used by the approval-triggered Celery flow; behavior differs from worker path |

The Celery worker uses Redis as broker/backend, retries broad `Exception` failures up to five times with backoff, and includes a daily token-guard task. The cron implementation separately enforces posting preferences and publishes due posts synchronously. The project should select one authoritative execution mechanism or clearly define how the two paths coordinate. More importantly, both paths need idempotency keys, row locking or atomic claims, and a durable external-post reconciliation strategy so retries cannot create duplicate social posts.[app/scheduler.py][19] [app/services/scheduler_service.py][20] [app/api/routes/cron.py][21]

### 2.6 Organizations, media, billing, and operations

The code has moved beyond the documented user-as-tenant MVP. Organizations contain roles such as owner, admin, member, and editor; members are represented through a join table; organizations also carry subscription tier and Stripe lifecycle fields. Content and media can be organization-scoped, and billing actions require owner/admin organization access.[app/models/organization.py][22] [app/api/routes/organizations.py][23] [app/api/routes/billing.py][24]

Media support is implemented even though the architecture documentation calls it post-MVP. Uploads accept image/video files, save them through a storage provider, and persist metadata and ownership. The local provider serves files at `/media/<filename>`, while Google Drive uploads are optionally made publicly readable. Making uploaded files public by default is a privacy and access-control decision that should be explicit, particularly for customer content.[app/services/storage.py][25] [app/api/routes/media.py][26]

Stripe billing includes checkout, customer portal, and webhook handling. This is a meaningful SaaS subsystem and should be documented, tested, and isolated from the core content workflow. Webhook processing must remain signature-verified, idempotent, and safe against repeated or out-of-order events.[app/api/routes/billing.py][24] [app/services/billing_service.py][27]

## 3. Frontend Analysis

The frontend is a single-page React application using Vite, TypeScript, Tailwind CSS, and React Router. Authenticated routes are wrapped by a common layout and organization context. The route map exposes dashboard, content list/create/detail/edit, Meta pages, social platforms, organizations, audit logs, users, insights, calendar, billing, and system settings.[frontend/src/App.tsx][28]

The content editor is the principal orchestration screen. It supports category selection, Gemini theme generation, media upload, AI optimization, optional organization selection, post-approval scheduling, and a Facebook-style live preview. This is a good product-level composition because it connects ideation, editing, approval preparation, media, and distribution intent in one workflow.[frontend/src/pages/ContentForm.tsx][29]

The shared API client correctly attaches the JWT stored under `content_platform_token`, handles JSON and `FormData`, and redirects to login on 401/403. However, `Platforms.tsx` reads a different local-storage key named `token` when constructing Facebook and LinkedIn OAuth redirect URLs. Because `AuthContext` stores the token under `content_platform_token`, the platform connection flow can receive a missing token. This is a concrete frontend integration defect and should be fixed by using the shared auth context or shared token constant rather than reading local storage directly.[frontend/src/api/client.ts][30] [frontend/src/context/AuthContext.tsx][31] [frontend/src/pages/Platforms.tsx][32]

The frontend build succeeds, but the UI still contains development-oriented shortcuts. Organization context hardcodes admin state, some authorization decisions are therefore presentation-only, and platform OAuth places a JWT in the URL query string. Query-string tokens can leak through browser history, reverse-proxy logs, analytics, referrers, and copied URLs. A safer pattern is a short-lived, single-use OAuth initiation code stored server-side and bound to the authenticated session.

## 4. Documentation Drift and Contract Mismatch

The largest project-level issue is that the documentation is not synchronized with the implementation. The README says authentication currently uses a `user_id` query parameter, while the runtime requires JWT bearer authentication. The older architecture document says JWT is future work, says media is deferred, and describes a smaller Facebook-only surface. The current code contains password authentication, organizations, media, LinkedIn, Instagram, Stripe, admin settings, and Celery workers.[README.md][1] [docs/ARCHITECTURE.md][33] [docs/IMPLEMENTATION_AND_REMAINING_DETAIL.txt][34]

| Topic | Older documentation says | Current code does | Impact |
|---|---|---|---|
| Authentication | `user_id` query parameter | JWT bearer token with password login | Setup instructions and tests are incorrect |
| Passwords | Future hashing | bcrypt hashes in `users.hashed_password` | Security documentation is stale |
| Organizations | Future/post-MVP | Implemented roles, membership, and billing | Product scope is understated |
| Media | Deferred | Local and Google Drive storage implemented | Architecture rules conflict with code |
| Platforms | Facebook-centered | Facebook, LinkedIn, Instagram | Endpoint and compliance documentation incomplete |
| Scheduling | Cron-oriented | Celery ETA tasks plus cron fallback | Operational runbook is ambiguous |
| Publishing state | Flat Facebook fields in older text | Per-target `ContentPublishStatus` rows | API/data model documentation is inconsistent |
| AI | Gemini theme generation | Theme generation plus content optimization | Feature and cost controls need documentation |

The repository needs a documentation reset. The recommended approach is to declare the current code as either a new versioned architecture or a deliberately reduced branch, then update the README, architecture, implementation tracker, frontend README, environment template, API examples, and deployment guide from the same source of truth.

## 5. Verification Results

The following checks were run against the checked-out project.

| Check | Result | Interpretation |
|---|---:|---|
| Python dependency installation | Completed | The declared requirements install successfully in the sandbox, although they downgrade several preinstalled packages to pinned versions |
| Python compilation | Passed | `python3 -m compileall -q app scripts` returned status 0 |
| Frontend production build | Passed | `tsc -b && vite build` completed successfully |
| Backend pytest suite | Failed: 5 failed, 2 passed | Tests are stale relative to the JWT-authenticated runtime and one async test lacks the required pytest plugin/structure |
| Docker Compose validation | Not run | Docker was not available in the sandbox environment |
| Frontend dependency audit | Findings | `npm audit --omit=dev` reported two high-severity issues in the React Router dependency range; the install summary reported 13 total findings including development dependencies |
| Git working tree | Clean | Build outputs and installed dependencies are ignored or outside tracked source |

The test failures are diagnostic rather than incidental. `tests/test_api.py` still calls protected VCE/content endpoints without a bearer token and expects the old `user_id` behavior. `tests/test_ai_service.py` declares an async test without awaiting asynchronous work, without importing `asyncio` for its direct execution path, and without a pytest async plugin. The file also catches exceptions rather than failing decisively, which can conceal broken AI behavior.[tests/test_api.py][35] [tests/test_ai_service.py][36] [tests/conftest.py][37]

## 6. Security and Reliability Findings

### High priority

| Finding | Evidence | Risk | Recommended action |
|---|---|---|---|
| Authentication contract is inconsistent | Runtime JWT versus stale query-param docs/tests | Misconfiguration, false confidence, broken onboarding | Make JWT the sole documented contract and rewrite fixtures/tests |
| Potential cross-tenant object access | `get_content()` and several route handlers operate by ID without a visible ownership check | IDOR/data exposure and unauthorized publishing/editing | Add a reusable ownership/org policy query to every content operation |
| Development secrets and demo credentials | Default `SECRET_KEY`; Docker startup seeds `admin/admin123` and `user1/password123` | Account takeover if deployed unchanged | Fail startup in production when secrets are default; never seed credentials in production |
| Token in OAuth query string | `Platforms.tsx` passes JWT as `?token=` | Credential leakage through logs/history/referrers | Use one-time server-side OAuth initiation records or secure session binding |
| Public media URLs by default | Local `/media` mount and Google Drive `anyone/reader` permission | Unintended content disclosure | Use private objects and short-lived signed URLs; require explicit public publishing |
| Broad admin configuration mutation | Admin can update arbitrary settings and sync them to `.env` | Runtime file/config tampering and secret exposure | Whitelist settings, audit changes, restrict filesystem writes, and remove `.env` mutation from the web process |

### Medium priority

| Finding | Evidence | Risk | Recommended action |
|---|---|---|---|
| Wildcard CORS with credentials | `allow_origins=["*"]`, `allow_credentials=True` | Browser credential policy and cross-origin exposure risk | Require explicit production origins and reject wildcard-plus-credentials configuration |
| Redis exposed on host | Compose publishes `6379:6379` | External access to broker/backend if host firewall is weak | Keep Redis internal to the Compose network and add authentication/TLS when required |
| Broad retry policy for publishing | Celery retries every `Exception` | Duplicate external posts and prolonged retries for permanent errors | Classify retryable errors and implement idempotency/reconciliation |
| Two scheduler paths | Celery and cron processors have different behavior | Duplicate posts, inconsistent limits, operational confusion | Choose one worker path and make the other a deliberate administrative fallback |
| SQLite shared by API and workers | API, Celery, and Beat share a file-mounted SQLite DB | Locking/contention and unsafe multi-process writes | Use PostgreSQL for multi-process production and add migrations |
| Missing rate limiting | Architecture document explicitly says it is not implemented | Abuse, brute-force login, API cost and social-platform quota pressure | Add Redis-backed limits for auth, AI, publishing, uploads, and admin endpoints |
| Configuration bug in settings service | `settings_service.py` uses `os` without importing it | GDrive diagnostics and `.env` sync can fail at runtime | Add the import and cover these routes with integration tests |
| Stale dependency risk | React Router audit findings; deprecated `google.generativeai` warning | Known client-side vulnerabilities and unmaintained AI SDK | Upgrade/replace affected packages, then run tests and lockfile review |

## 7. Engineering Quality Assessment

The code is organized into recognizable route, service, model, schema, and core layers, and several important operations correctly use atomic content-plus-audit transactions. The per-destination publishing model and organization membership checks are good foundations. The frontend is also cohesive enough to build successfully and presents a broad, understandable product workflow.[app/services/audit_service.py][38] [app/services/content_service.py][16]

The main quality weakness is not basic compilation; it is **contract consistency**. The code, tests, documentation, and deployment instructions describe different generations of the product. This makes it difficult to determine whether a failure is a regression, an expected behavior change, or an undocumented feature. The project status document’s claim of being fully verified is not supported by the current pytest result.[docs/PROJECT_STATUS_SUMMARY.md][39]

The application also lacks a conventional migration system. `create_all()` and hand-written SQLite alterations in `scripts/init_db.py` may work for a small local deployment but do not provide reliable forward/backward schema management, rollback, or coordinated upgrades across API and worker processes. Introducing Alembic or an equivalent migration tool should precede production PostgreSQL adoption.

## 8. Recommended Prioritized Roadmap

### Phase 0: Establish one source of truth

First, freeze feature additions briefly and reconcile the implementation with the documentation. Decide whether the current organization/media/multiplatform/billing system is the intended product baseline. Update the README, architecture, implementation tracker, frontend README, environment template, route inventory, and Docker runbook. Record the supported authentication contract as JWT and remove obsolete `user_id` examples.

### Phase 1: Repair verification and authorization

Rewrite pytest fixtures to create users, issue JWTs, and test authenticated and unauthenticated behavior. Add tests for content ownership, organization membership, approval transitions, publishing authorization, media access, admin settings, billing webhook signature validation, and maintenance mode. Add frontend lint/build checks to CI. Make the AI test either a deterministic unit test with a mocked provider or a separately opt-in integration test that never runs against a live API key in normal CI.

At the same time, centralize authorization. Every content read, mutation, insight lookup, scheduled-post operation, and publish request should resolve the target through an access-controlled query. Organization roles should be enforced in backend dependencies/services, not inferred in frontend state.

### Phase 2: Harden secrets and external integrations

Require non-default `SECRET_KEY`, encryption key, and administrative bootstrap behavior in production. Remove demo passwords from production startup. Replace OAuth JWT query-string transport with a one-time server-side flow. Make media private by default, add file size/type/content validation, and add cleanup for abandoned uploads. Implement explicit retry classification and idempotency for Facebook, LinkedIn, Instagram, and Stripe webhook operations.

### Phase 3: Consolidate scheduling and persistence

Select Celery or cron as the canonical scheduler. If Celery remains canonical, make the cron endpoint an administrative recovery tool that claims rows safely and cannot race the worker. Add unique execution keys, atomic status transitions, row locking, external-post reconciliation, and metrics. Move API/worker deployments to PostgreSQL with migrations and keep Redis internal to the deployment network.

### Phase 4: Dependency, observability, and release discipline

Upgrade the vulnerable React Router range and replace the deprecated Gemini SDK with its supported successor. Pin and regularly review both Python and npm dependencies. Add structured logs, request IDs propagated to worker tasks, metrics for publishing outcomes, token expiry, queue lag, and webhook failures, plus a documented backup/restore procedure. Establish CI gates for Python tests, frontend build/lint, dependency audit, migration validation, and container startup.

## 9. Suggested First Commits

A practical next sequence would be:

1. **`docs: reconcile architecture and authentication contract`** — update all stale JWT/query-param, media, platform, scheduler, and organization documentation.
2. **`test: rebuild authenticated fixtures and workflow coverage`** — replace the current unauthenticated tests and repair the AI test structure.
3. **`security: enforce production secrets and remove demo bootstrap credentials`** — fail safely on defaults and separate development seeding from production startup.
4. **`auth: fix platform OAuth initiation`** — remove the `localStorage.getItem('token')` mismatch and eliminate JWTs from query strings.
5. **`authz: enforce content ownership and organization policies`** — cover every content operation, insights path, scheduled post, and publishing target.
6. **`scheduler: consolidate execution and add idempotency`** — define one authoritative worker path and make external publication retry-safe.
7. **`ops: add migrations and production Compose profile`** — introduce migrations, PostgreSQL, private Redis, health checks, and separate worker deployment configuration.

## 10. Final Conclusion

The repository has a substantial amount of implemented product functionality and a reasonable modular shape. Its strongest design decisions are the approval workflow, audit-oriented service layer, per-destination publishing status, organization model, and composable frontend editor. Its weakest aspect is the gap between what the repository claims and what the runtime actually does.

The project is therefore best understood as a **feature-rich but insufficiently reconciled pre-production SaaS platform**. The most valuable work now is not another integration; it is making the existing system trustworthy: one documented contract, verified authorization boundaries, reliable tests, safe secret/configuration handling, deterministic scheduling, migration support, and dependency hygiene.

## References

[1]: `README.md` — Top-level feature list, setup instructions, documented API, and older MVP authentication model.
[2]: `app/api/routes/__init__.py` — Central router registration and maintenance-mode dependency.
[3]: `app/models/content.py` — Content status, ownership, organization, media, and scheduling fields.
[4]: `app/models/content_execution.py` — Per-destination publishing status model.
[5]: `app/core/config.py` — Runtime settings, defaults, secrets, CORS, storage, and integration configuration.
[6]: `scripts/init_db.py` — Database initialization, schema adjustments, and sample data seeding.
[7]: `docker-compose.yml` — API, Redis, Celery, Celery Beat, volumes, and environment configuration.
[8]: `app/main.py` — FastAPI lifecycle, middleware, exception handling, mounts, and SPA serving.
[9]: `app/core/database.py` — SQLAlchemy engine, sessions, and `create_all()` initialization.
[10]: `app/api/dependencies.py` — JWT validation, admin checks, and maintenance-mode gating.
[11]: `app/api/routes/auth.py` — Signup, login, password verification, JWT issuance, and logout.
[12]: `app/core/security.py` — JWT and bcrypt/Passlib security primitives.
[13]: `app/api/routes/content.py` — Content endpoint authorization and publishing/insights handlers.
[14]: `app/api/routes/admin_settings.py` — Super-admin configuration and operational controls.
[15]: `frontend/src/context/OrgContext.tsx` — Frontend organization context and admin placeholder.
[16]: `app/services/content_service.py` — Content business rules, organization checks, state transitions, and audit transactions.
[17]: `app/services/fb_api.py` — Facebook/Instagram publishing and per-target status behavior.
[18]: `app/schemas/content.py` — Current content API schemas and multi-target publishing requests.
[19]: `app/scheduler.py` — Celery scheduling, retries, publishing task, and token guard.
[20]: `app/services/scheduler_service.py` — Synchronous cron scheduler, safety limits, and audit behavior.
[21]: `app/api/routes/cron.py` — Secret-protected cron endpoint.
[22]: `app/models/organization.py` — Organization roles, tiers, membership, and subscription fields.
[23]: `app/api/routes/organizations.py` — Organization and membership API.
[24]: `app/api/routes/billing.py` — Stripe checkout, portal, and webhook endpoints.
[25]: `app/services/storage.py` — Local and Google Drive media storage providers.
[26]: `app/api/routes/media.py` — Media upload and access endpoints.
[27]: `app/services/billing_service.py` — Stripe customer/subscription and quota behavior.
[28]: `frontend/src/App.tsx` — Frontend route map and auth/org providers.
[29]: `frontend/src/pages/ContentForm.tsx` — Content editor, AI, media, organization, and scheduling workflow.
[30]: `frontend/src/api/client.ts` — Shared API fetch wrapper and JWT header behavior.
[31]: `frontend/src/context/AuthContext.tsx` — Frontend JWT persistence under `content_platform_token`.
[32]: `frontend/src/pages/Platforms.tsx` — Platform OAuth initiation and inconsistent `token` key usage.
[33]: `docs/ARCHITECTURE.md` — Locked but stale architecture and future-JWT/media assumptions.
[34]: `docs/IMPLEMENTATION_AND_REMAINING_DETAIL.txt` — Stale implementation tracker and old authentication assumptions.
[35]: `tests/test_api.py` — Unauthenticated tests that still expect query-parameter identity.
[36]: `tests/test_ai_service.py` — Async test without pytest async support and weak failure handling.
[37]: `tests/conftest.py` — In-memory database fixture without authenticated user/token setup.
[38]: `app/services/audit_service.py` — Audit log creation behavior.
[39]: `docs/PROJECT_STATUS_SUMMARY.md` — Project status claims and declared verification state.
