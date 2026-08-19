# Auto Post Generation and Auto Publishing — Phase-Wise Implementation Plan

**Project:** `fb-post-automated-creator`  
**Baseline commit:** `9b7156d` on `main`  
**Source analysis:** [`AUTO_POST_DEEP_ANALYSIS.md`](./AUTO_POST_DEEP_ANALYSIS.md)  
**Objective:** Evolve the current AI-assisted drafting and user-scheduled Facebook publishing workflow into a reliable, auditable, plan-based auto post generation and publishing system.

## 1. Target Product Definition

The implementation should not jump directly from today’s manual drafting flow to unrestricted autonomous posting. The safest product progression is to introduce three explicit automation modes:

| Mode | Behavior | Initial release |
|---|---|---:|
| **Assisted** | AI suggests themes or complete drafts; the user edits and creates the draft | Already partially available |
| **Approval-required autopilot** | The system generates complete drafts on a schedule, persists them as `DRAFT`, and submits them for human approval; approved posts are scheduled automatically | **First automation milestone** |
| **Controlled autopilot** | The system generates, validates, and publishes within explicit organization/page policies and quotas | Later, opt-in only |

The default must remain **approval-required**. Automatic content generation and automatic publishing should be separate permissions. An organization may allow generation while still requiring human approval; publishing must never be enabled merely because AI generation is enabled.

> **Target first release:** The system automatically generates a complete post draft at a configured time, stores it with full provenance, requests approval, and publishes it only after approval through a reliable, idempotent worker.

The existing project currently generates theme ideas but does not persist complete AI-generated posts, while scheduled publishing starts only after manually authored content is approved.[AUTO_POST_DEEP_ANALYSIS.md][1] [app/schemas/content.py][2] [app/services/content_service.py][3]

## 2. Architecture Principles

The new implementation should preserve the existing monolithic FastAPI architecture while introducing durable job and campaign boundaries. Long-running AI and social-platform operations should run in background workers, not inside ordinary HTTP requests. Every automatic action must be attributable to a user, organization, plan, job, model/provider, and external request.

The system should use these principles:

1. **Human approval by default.** No generated content should publish simply because an AI call succeeded.
2. **Deterministic job ownership.** Every generation and publishing operation receives a unique idempotency key.
3. **Structured AI output.** The model must return schema-validated JSON, not newline-split free text.
4. **Policy before execution.** Safety limits, page ownership, organization access, quotas, token validity, and content checks must be evaluated before enqueueing or publishing.
5. **One canonical executor.** Celery should become the sole production execution path; the current cron processor should be a controlled recovery/admin path or be removed after migration.[app/scheduler.py][4] [app/services/scheduler_service.py][5]
6. **Truthful statuses.** Parent job status must reflect the real per-target outcome, including partial failure.
7. **Full auditability.** The system must record what was generated, by which model, from which plan, who approved it, what was published, and why any attempt failed.
8. **Safe rollout.** New automation should first operate in dry-run and approval-required modes before any controlled autonomous publishing is enabled.

## 3. Phase Overview

| Phase | Name | Primary outcome | Depends on |
|---|---|---|---|
| 0 | Product contract and baseline freeze | One authoritative automation contract and status vocabulary | None |
| 1 | Foundation stabilization | Correct auth, ownership, tests, AI runtime, and existing publishing statuses | Phase 0 |
| 2 | Complete-post generation | AI can generate validated title/body drafts and persist provenance | Phase 1 |
| 3 | Generation plans and campaigns | Users can define recurring generation schedules and target pages | Phase 2 |
| 4 | Reliable publishing executor | Scheduled posts execute idempotently with policy checks and truthful failures | Phase 1, preferably Phase 3 |
| 5 | Frontend automation control plane | Users can create plans, review drafts, approve/reject, monitor jobs, and recover failures | Phases 2–4 |
| 6 | Validation and controlled rollout | CI, observability, dry-run, approval-required production release, and later opt-in autopilot | Phases 1–5 |

A practical implementation order is **Phase 0 → Phase 1 → Phase 2 → Phase 4 → Phase 3 → Phase 5 → Phase 6** if reliable manual scheduling is urgent. If the product team wants recurring AI generation before improving publishing reliability, implement Phase 3 after Phase 2 but keep all output in approval-required mode.

## Phase 0 — Product Contract and Baseline Freeze

### Objective

Resolve the mismatch between the current code, documentation, and product language before adding new automation. The existing repository calls theme suggestions “AI theme generation,” while the desired product requires complete post generation and automatic creation.[README.md][6] [AUTO_POST_DEEP_ANALYSIS.md][1]

### Implementation work

Update the following documents and remove obsolete assumptions:

| Area | Required change |
|---|---|
| Authentication | Document JWT bearer authentication as the only runtime contract; remove `user_id` query-parameter examples |
| AI generation | Define “theme suggestion,” “complete draft generation,” and “autonomous publishing” as separate capabilities |
| Approval | State that approval-required mode is the default and controlled autopilot is opt-in |
| Scheduling | Declare Celery as the canonical executor and define cron as recovery-only, if retained |
| Publishing | Make `ContentPublishStatus` the source of truth for per-target execution |
| Organizations | Document organization roles, quotas, and page ownership |
| Media | Document local/Google Drive storage and the privacy model |
| Statuses | Define shared status enums for generation, approval, scheduling, publishing, retrying, and dead-letter states |

### Deliverables

- Updated `README.md`.
- Updated `docs/ARCHITECTURE.md` or a new versioned architecture document.
- Updated `docs/IMPLEMENTATION_AND_REMAINING_DETAIL.txt`.
- Updated `frontend/README.md`.
- Updated `.env.example` and deployment documentation.
- A product decision record defining the three automation modes.

### Acceptance criteria

The product team can answer, without ambiguity:

1. Does AI create a complete title/body or only suggest themes?
2. Who approves generated content?
3. Can any organization enable automatic publishing?
4. Which worker executes scheduled posts?
5. What does `POSTED`, `FAILED`, `PARTIALLY_FAILED`, `RETRYING`, and `DEAD_LETTER` mean?

## Phase 1 — Foundation Stabilization

### Objective

Make the current system safe and testable before building autonomous generation. This phase fixes the P0 defects identified in the deep analysis.

### 1.1 Fix authentication and ownership boundaries

Create reusable access-control functions such as:

```python
get_owned_content(db, content_id, user)
get_accessible_page(db, meta_page_id, user)
get_accessible_schedule(db, scheduled_post_id, user)
require_org_role(db, organization_id, user, allowed_roles)
```

Use these functions for content detail, update, submit, approval, delete, insights, Facebook publishing, LinkedIn publishing, scheduled-post creation, and media attachment. The current list path applies user filtering, but detail and action paths must be reviewed as a complete set.[app/api/routes/content.py][7] [app/services/content_service.py][3]

Fix the frontend OAuth token mismatch: `AuthContext` stores `content_platform_token`, while `Platforms.tsx` reads `token`. Move OAuth initiation into a shared auth helper and stop placing bearer JWTs in query strings. Use a short-lived, one-time server-side OAuth initiation code instead.[frontend/src/context/AuthContext.tsx][8] [frontend/src/pages/Platforms.tsx][9]

### 1.2 Fix AI service runtime behavior

Add the missing Gemini import in `app/services/ai_service.py`, standardize the provider SDK/model configuration, and replace silent exceptions with typed error classes. Add provider timeouts, bounded retries, and structured logs without exposing the API key or prompt contents unnecessarily.[app/services/ai_service.py][10] [app/services/theme_generation_service.py][11]

### 1.3 Correct publishing status semantics

Change the publishing service to return a structured result such as:

```python
PublishBatchResult(
    attempted=2,
    posted=1,
    failed=1,
    target_results=[...],
)
```

The scheduler must mark the parent scheduled job `POSTED` only when the target outcome is successful. Add `PARTIALLY_FAILED` when some destinations succeed and others fail. The current Facebook service catches per-page errors and returns normally, allowing the Celery task to mark the parent `POSTED` even when the target status is `FAILED`.[app/services/fb_api.py][12] [app/scheduler.py][4]

### 1.4 Rebuild automated tests

Replace stale query-parameter fixtures with authenticated JWT fixtures. Add deterministic mocks for Gemini and Meta Graph API calls. Tests must not require live credentials.

| Test group | Minimum coverage |
|---|---|
| Auth | Signup, login, inactive user, expired/invalid token, admin access |
| Content | Create, update, submit, approve, reject, delete, ownership isolation |
| AI | Valid structured output, malformed output, missing key, provider timeout |
| Scheduling | Approved-only, future-time validation, page ownership, duplicate prevention |
| Publishing | Text, image, video, invalid token, rate limit, partial failure, retry classification |
| Workers | Claiming, duplicate task, retry, final failure, cancellation |
| Organizations | Member roles, quota access, cross-org isolation |

### Phase 1 acceptance criteria

- All existing backend tests are migrated to JWT and pass.
- Frontend build and lint pass.
- `AIService` can be tested with a mocked provider.
- Cross-user content and page operations return 404/403 as designed.
- A failed Facebook target cannot produce a false parent `POSTED` status.
- No default production secret or demo password is accepted in production mode.

## Phase 2 — Reliable Complete-Post Generation

### Objective

Convert the current theme-only Gemini helper into a complete, structured, auditable post-generation service. The output should initially become a draft requiring approval.

### 2.1 Add generation data model

Introduce these tables through a migration framework:

```text
content_generation_jobs
content_generation_variants
content_generation_usage
```

Suggested fields:

| Entity | Important fields |
|---|---|
| `ContentGenerationJob` | `id`, `organization_id`, `requested_by_id`, `plan_id`, `status`, `idempotency_key`, `input_json`, `model`, `provider`, `provider_request_id`, `error_code`, `retry_count`, timestamps |
| `ContentGenerationVariant` | `id`, `job_id`, `title`, `body`, `hook`, `cta`, `hashtags_json`, `media_prompt`, `risk_flags_json`, `validation_status`, `selected_at` |
| `ContentGenerationUsage` | `organization_id`, `job_id`, input/output tokens, estimated cost, provider, model, created_at |

Add `generated_by_ai`, `generation_job_id`, `generation_variant_id`, and `content_fingerprint` to `Content` or a linked provenance table. Do not overload the existing title/body columns with invisible AI metadata.

### 2.2 Implement a structured generation contract

Replace the current line-oriented theme output with schema-validated JSON:

```json
{
  "title": "A concise post title",
  "body": "The complete post body",
  "hook": "The opening hook",
  "call_to_action": "A clear optional CTA",
  "hashtags": ["#example"],
  "media_prompt": "Optional visual direction",
  "language": "en",
  "risk_flags": []
}
```

Validate:

- Title and body length.
- Language and encoding.
- Empty or repeated content.
- Prohibited words and platform restrictions.
- Organization brand voice and required disclaimers.
- Duplicate similarity against recent content.
- Prompt-injection or untrusted extra instructions.
- Category/template consistency.

If validation fails, the job must enter `VALIDATION_FAILED` rather than silently returning an empty list.

### 2.3 Add generation API

Add endpoints such as:

```text
POST /api/v1/generation/preview
POST /api/v1/generation/jobs
GET  /api/v1/generation/jobs/{id}
POST /api/v1/generation/jobs/{id}/select
POST /api/v1/generation/jobs/{id}/persist-draft
```

`preview` may synchronously return a result for a fast user interaction, but production generation should use the durable job path. `persist-draft` should create a normal `Content` row in `DRAFT` status with complete provenance and an audit record.

### 2.4 Enforce quotas and cost controls

Connect generation calls to organization tier limits. Before a job is queued, verify monthly generation count, estimated token budget, media requirements, and plan entitlement. Persist provider/model/token/cost information for billing and operational reporting.

### Phase 2 acceptance criteria

- One request can generate one or more complete title/body variants.
- Every persisted AI draft has generation provenance.
- Generated content never publishes directly in the default mode.
- Invalid or malformed model output is rejected safely.
- AI failures have visible status and actionable error messages.
- Usage and estimated cost are recorded per organization.
- A mocked integration test covers the entire generation-to-draft path.

## Phase 3 — Generation Plans and Campaigns

### Objective

Allow users to define what should be generated and when, without requiring them to manually open the content form for every post.

### 3.1 Add generation-plan model

Introduce:

```text
content_generation_plans
content_generation_plan_targets
content_generation_runs
```

Suggested plan fields:

| Field | Purpose |
|---|---|
| `organization_id` | Tenant boundary |
| `created_by_id` | Owner/audit identity |
| `name` | Human-readable plan name |
| `category_id` | Content category |
| `template_id` | Hook/template selection |
| `brand_voice_json` | Tone, language, style, banned terms |
| `platforms_json` | Facebook/LinkedIn/Instagram targets |
| `page_ids_json` | Target destinations |
| `recurrence_rule` | Daily/weekly/selected days/one-time |
| `preferred_time_zone` | Correct local scheduling |
| `preferred_times_json` | Generation/publishing slots |
| `approval_mode` | `required` or controlled opt-in |
| `active` | Enable/disable plan |
| `max_posts_per_day` | Plan-level safety cap |
| `cooldown_minutes` | Page-level safety cap |
| `next_run_at` | Scheduler cursor |

### 3.2 Define plan execution

A plan run should:

1. Atomically claim the due plan occurrence.
2. Check organization quota and page safety limits.
3. Generate one or more variants.
4. Run moderation, duplication, and brand-policy checks.
5. Persist a draft with `generation_job_id` and plan provenance.
6. If `approval_mode=required`, create an approval task and stop.
7. If controlled auto-approval is enabled, record the policy decision and continue only if every check passes.
8. Create the publishing occurrence only after the content is approved.
9. Move the plan cursor to the next recurrence only after the run has a durable terminal state.

### 3.3 Add plan APIs

```text
POST   /api/v1/generation-plans/
GET    /api/v1/generation-plans/
GET    /api/v1/generation-plans/{id}
PATCH  /api/v1/generation-plans/{id}
POST   /api/v1/generation-plans/{id}/pause
POST   /api/v1/generation-plans/{id}/resume
POST   /api/v1/generation-plans/{id}/run-now
GET    /api/v1/generation-plans/{id}/runs
POST   /api/v1/generation-plans/{id}/preview
```

`run-now` must still respect quotas, ownership, safety rules, and approval mode. It must not bypass approval.

### Phase 3 acceptance criteria

- A user can create a daily or weekly plan for a selected page.
- The system generates a complete draft at the configured time without opening the content form.
- Approval-required plans stop at a reviewable draft.
- Pausing a plan prevents new runs but does not corrupt existing drafts or queued posts.
- Time zones and daylight-saving transitions are tested.
- Duplicate plan runs are prevented by an idempotency key.

## Phase 4 — Reliable Autonomous Publishing Executor

### Objective

Make scheduled execution safe, truthful, and retryable. This phase is required before controlled autopilot is enabled.

### 4.1 Choose one execution path

Use Celery/Redis as the canonical worker path. Retain `POST /api/v1/cron/run` only as a privileged recovery endpoint that invokes the same job-claiming service. Do not maintain separate business rules in `scheduler_service.py` and `scheduler.py`.[app/scheduler.py][4] [app/services/scheduler_service.py][5]

### 4.2 Add a durable execution state machine

Use explicit states:

```text
PENDING
CLAIMED
PROCESSING
RETRYING
POSTED
PARTIALLY_FAILED
FAILED
DEAD_LETTER
CANCELLED
```

Add `attempt_count`, `next_retry_at`, `last_error_code`, `last_error_message`, `worker_id`, `idempotency_key`, `external_post_id`, and `completed_at` fields.

### 4.3 Make execution idempotent

Implement all of the following:

- Unique key for `(content_id, target_platform, target_id, occurrence_id)`.
- Atomic claim using a database update from `PENDING` to `CLAIMED`.
- Skip execution when a successful external post ID already exists.
- Persist a deterministic client idempotency key where the platform supports it.
- Reconcile ambiguous timeouts before retrying.
- Prevent double-click duplicate scheduling at the API layer.
- Add a unique constraint for one execution record per content occurrence and target.

### 4.4 Apply policies inside the executor

Before calling Facebook, validate:

- Content is approved.
- Page still belongs to the user/organization.
- Page token exists and is not known expired.
- Organization subscription and quota permit execution.
- Cooldown and max-per-day limits permit execution.
- Content has not already been published to the target.
- Media still exists and is accessible.
- Target platform is enabled for the plan.

### 4.5 Classify external failures

| Error | State | Retry behavior |
|---|---|---|
| Invalid/expired token | `FAILED` with `AUTH_REQUIRED` | No automatic retry; require reconnect |
| Permission denied | `FAILED` with `PERMISSION_DENIED` | No retry until configuration changes |
| Rate limit/429 | `RETRYING` | Provider-aware exponential backoff |
| Timeout/network error | `RETRYING` | Bounded retry, then dead letter |
| Invalid media/content | `FAILED` | No retry; user correction required |
| Unknown 5xx | `RETRYING` | Bounded retry and alert |
| Ambiguous external result | `PROCESSING`/reconciliation | Query provider or manual review before retry |

### Phase 4 acceptance criteria

- A failed target never produces a false `POSTED` parent status.
- Retrying a worker task cannot create a duplicate post.
- Safety limits apply identically to Celery and recovery cron.
- Cancelled jobs cannot publish after cancellation.
- Retry exhaustion creates `DEAD_LETTER` and an actionable audit event.
- The dashboard displays actual execution state, not inferred schedule intent.

## Phase 5 — Frontend Automation Control Plane

### Objective

Expose the new automation capabilities clearly and truthfully in the UI.

### Required screens

| Screen | Required functionality |
|---|---|
| Automation Plans | Create, edit, pause, resume, duplicate, and delete generation plans |
| Plan Builder | Category, tone, language, brand voice, target pages, frequency, time zone, approval mode |
| Generation Queue | View pending, running, failed, and completed generation jobs |
| Draft Review | Compare variants, inspect AI provenance, edit content, approve/reject, request regeneration |
| Publishing Queue | View pending, processing, retrying, posted, partial, failed, and dead-letter jobs |
| Failure Detail | Show safe error, retry eligibility, reconnect/configure actions, and audit trail |
| Usage/Billing | Show generation count, token/cost estimate, plan limits, and publishing quota |
| Calendar | Show actual occurrences and execution status; support pause/cancel/retry where allowed |

### UI rules

- Never label content `READY` unless a real scheduled execution exists.
- Never claim “infinite retry” when the worker has bounded retries.
- Show whether a generated draft is awaiting human approval.
- Show the target page, scheduled time zone, approval policy, and last execution result.
- Use the shared auth context and API client rather than reading token keys directly.

### Phase 5 acceptance criteria

- A user can create a plan without manually creating a content row.
- Generated drafts appear in an approval queue.
- Users can distinguish generation failure from publishing failure.
- Users can pause a plan without deleting existing content.
- Dashboard and calendar display the same source-of-truth status.
- All privileged actions are enforced by the backend, not only hidden in the UI.

## Phase 6 — Validation, Release, and Controlled Autopilot

### 6.1 Test strategy

Create four automated layers:

| Layer | Scope |
|---|---|
| Unit tests | Prompt construction, JSON parsing, validators, policy checks, retry classification |
| Service tests | Generation-to-draft, approval transitions, plan execution, publishing result aggregation |
| API tests | JWT, org access, plan CRUD, job status, approval, schedule, cancel, retry |
| Integration tests | Mocked Gemini, mocked Meta Graph API, Redis/Celery test worker, migration startup |

Add property tests for idempotency and state transitions. Test race conditions by submitting duplicate schedule/create requests and executing the same worker task concurrently.

### 6.2 Observability

Add structured events and metrics:

```text
generation_job_created
 generation_succeeded
 generation_failed
 content_draft_created
 approval_requested
 content_approved
 publish_job_claimed
 publish_succeeded
 publish_partial_failure
 publish_retry_scheduled
 publish_dead_lettered
 token_reauth_required
 quota_blocked
```

Track generation latency, AI failure rate, token usage, estimated cost, approval turnaround, queue lag, publish success rate, retry rate, duplicate prevention events, and per-page rate-limit failures.

### 6.3 Rollout stages

| Rollout stage | Enabled behavior | Exit criteria |
|---|---|---|
| Dry run | Generate and validate but do not persist/publish | No critical validation or cost-control defects |
| Approval-required | Persist drafts and require human approval | Reliable generation, approval, and publishing metrics |
| Limited pilot | One organization, one page, small daily cap | No duplicate posts; truthful statuses; acceptable failure recovery |
| Controlled autopilot | Opt-in org/page policy with strict caps | Security review, rollback tested, dead-letter workflow operational |
| General availability | Broader rollout with plan-based quotas | SLOs, alerts, backups, and incident runbook complete |

### 6.4 Production readiness checklist

- PostgreSQL and migrations replace shared SQLite for API/worker production.
- Redis is private to the deployment network and protected.
- Non-default `SECRET_KEY`, token encryption key, and admin bootstrap are mandatory.
- Demo credentials are never seeded in production.
- Media is private by default and served through signed URLs.
- Rate limiting exists for login, AI, upload, publishing, and admin endpoints.
- Frontend dependency vulnerabilities are resolved and lockfiles are reviewed.
- Backups and restore testing are documented.
- Worker health, queue lag, and dead-letter alerts are configured.
- A kill switch can pause all generation and publishing plans.

## 4. Recommended Immediate Sprint

Before starting the larger campaign system, implement the following small, high-value sprint:

1. Fix the missing `genai` import and add mocked AI tests.
2. Fix the Celery parent-status bug when target publishing fails.
3. Add future-time validation and duplicate schedule protection.
4. Unify safety-limit checks in the canonical executor.
5. Replace stale tests with JWT-authenticated fixtures.
6. Fix the frontend `token` versus `content_platform_token` mismatch.
7. Correct Calendar so it reads actual scheduled-post rows and truthful statuses.
8. Add `PARTIALLY_FAILED`, `RETRYING`, and `DEAD_LETTER` states.
9. Add basic audit events for generation and publishing attempts.
10. Update the README and implementation tracker to reflect the true automation boundary.

This sprint creates the minimum safe foundation for Phase 2 complete-post generation.

## 5. Final Success Definition

The implementation is complete only when this scenario works reliably:

1. An organization owner creates an automation plan for a Facebook page.
2. At the configured time, the system creates a generation job with an idempotency key.
3. Gemini returns structured complete-post variants.
4. The system validates content, brand policy, duplication, quota, and cost.
5. A draft is persisted with AI provenance.
6. The responsible reviewer receives an approval task.
7. After approval, one immutable publishing occurrence is created.
8. The worker claims it exactly once and applies page safety policies.
9. Facebook returns an external post ID.
10. The database records the external ID and truthful `POSTED` state.
11. If Facebook fails, the system classifies the error, retries only when safe, and exposes a recovery action.
12. Every step is visible in audit logs and operational metrics.

Until this scenario is implemented and tested, the product should continue to be marketed internally as **AI-assisted drafting with scheduled publishing**, not as complete autonomous autopilot.

## References

[1]: `AUTO_POST_DEEP_ANALYSIS.md` — Focused analysis of current automation boundaries, missing autonomous generation, and priority defects.
[2]: `app/schemas/content.py` — Manual title/body content contract and optional schedule fields.
[3]: `app/services/content_service.py` — Draft creation, approval workflow, audit logging, and schedule enqueue after approval.
[4]: `app/scheduler.py` — Current Celery ETA scheduling, retries, worker execution, and token guard.
[5]: `app/services/scheduler_service.py` — Separate cron-style scheduler and safety-limit implementation.
[6]: `README.md` — Existing project feature and setup documentation.
[7]: `app/api/routes/content.py` — Content route handlers and current access-control surface.
[8]: `frontend/src/context/AuthContext.tsx` — Shared frontend JWT storage convention.
[9]: `frontend/src/pages/Platforms.tsx` — Platform OAuth flow with inconsistent local-storage token key.
[10]: `app/services/ai_service.py` — Current Gemini optimization service.
[11]: `app/services/theme_generation_service.py` — Current Gemini theme-generation service.
[12]: `app/services/fb_api.py` — Per-page publishing results and failure handling.
