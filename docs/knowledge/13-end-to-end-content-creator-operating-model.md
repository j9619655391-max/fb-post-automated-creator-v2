# End-to-End Content Creator Operating Model

## Purpose

The platform should behave like a workspace-aware content operating system, not a collection of isolated endpoints. The end-to-end contract begins with client context and ends with a measured, auditable, human-approved result.

## Pipeline

| Stage | Input | Output | Human control |
|---|---|---|---|
| Workspace setup | Business/page details, language, voice, palette, sources | Workspace profile and source states | User enters and approves context |
| Intelligence | Profile, approved/pending sources, history | Category ranking, evidence, opportunities | User can override recommendation |
| Brief | Category, objective, pillar, template, platform | Structured creative brief | User reviews brief |
| Preview | Brief and sample copy | Local preview without media/AI mutation | User chooses template and edits copy |
| Confirmation | Reviewed brief | Explicit generation permission | Checkbox/confirm required |
| Generation | Confirmed brief and provider | AI draft copy and usage record | No publishing permission implied |
| Quality gates | Draft copy/image/package | Moderation, duplicate, contrast, grounding results | User sees flags and reasons |
| Package | Approved brief + variants | Facebook/Instagram/LinkedIn package | User compares variants |
| Human approval | Complete package | Approved/rejected/revision state | Operator decision required |
| Scheduling/publishing | Approved target and policy | Provider attempt and audit event | Separate confirmation for external action |
| Learning | Metrics and feedback | Updated recommendations and templates | Human feedback remains auditable |

## Cross-module invariants

The active workspace must be present at every stage. Category and business objective must agree. Language must remain consistent. Blank contact data must remain blank. Generated media must be tied to the workspace. Draft status must remain distinct from approval and publishing. Provider failures must not be hidden behind generic success messages. No external action is implied by a preview or by AI generation.

## Failure containment

Each stage should fail locally with an explanation and preserve the previous valid state. A source verification failure should not block all manual content; it should lower factual confidence. A moderation failure should not delete the draft; it should mark it for revision. A provider failure should not create a duplicate post. A rejected draft should not delete older content. A failed scheduled attempt should move through retry or dead-letter policy with an audit trail.

## Product surfaces

| Surface | Responsibility |
|---|---|
| Workspace Knowledge | Context, sources, categories, language, brand tokens |
| New Content | Brief, preview, confirmation, draft generation |
| Creative Studio | Image archetypes, copy package, preview, compose confirmation |
| Content Detail | Full package, flags, revisions, approval action |
| Scheduler/Autopilot | Approved targets, caps, cooldowns, retries |
| Platforms | OAuth, readiness, page/account selection |
| Analytics/Insights | Performance and learning signals |
| Billing | Usage, cost, limits, provider metadata |
| Audit Logs | Traceability for every sensitive mutation |

## Readiness definition

The platform is production-ready for a workspace only when profile context is complete enough, sources are understood, template/brand tokens are configured, moderation and duplicate checks pass, approval controls are active, provider readiness is verified, publishing policies are enforced, and the operator can explain every external mutation. “AI generation works” alone is not production readiness.

## Test strategy

Use focused unit tests for each service, API tests for contracts and permissions, integration tests for state transitions, renderer tests for dimensions/contrast/overflow, and browser smoke tests for the operator workflow. Mock external providers. A final end-to-end smoke test should prove that selecting a workspace and changing options does not create media; only explicit confirmation should create a draft; and no draft publishes without separate approval.

## Future evolution

The knowledge library should be versioned with the product. Every major change to prompt policy, template archetype, provider adapter, approval state, or data model should update its module study and index. Research documents guide decisions but do not replace tests, audit logs, or user confirmation.
