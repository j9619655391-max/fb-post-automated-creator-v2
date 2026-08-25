# End-to-End Browser Audit Matrix

## Scope and safety

This audit verifies the platform against the durable knowledge library and the live authenticated browser application at `http://localhost:8000`. It will not publish, schedule, boost, send Telegram messages, connect OAuth, submit content for approval, delete data, replace existing drafts, or mutate provider accounts. Local unscheduled drafts may be created only through an explicit confirmation gate and will remain in draft state.

The phrase “three separate cases per module” is implemented as three independent cases for each content-oriented module. For technical modules—provider readiness, scheduler safety, analytics, billing, and audit—the three cases are safe browser checks or mocked/local validation cases rather than external actions.

## Case design

| Case class | Meaning |
|---|---|
| C1 | Normal happy path for the module |
| C2 | Boundary, variation, or alternate category/platform path |
| C3 | Failure, warning, duplicate, or safety path |

## Audit matrix

| Track | C1 | C2 | C3 | Expected evidence |
|---|---|---|---|---|
| Workspace and knowledge | Quote workspace profile/languages/approval state | Empty optional URLs remain blank and save | Category evidence and workspace isolation | Browser fields, save status, recommendation evidence |
| Quote category and Hinglish generation | Truth quote in natural Hinglish | Love or Motivation quote with alternate archetype | Pain quote with sensitive-language safety review | Brief, prompt context, draft copy, category/template match |
| Creative templates and images | Centered Gallery or Editorial Split | Paper Note/Brush Frame/Type Poster variant | Long quote routes/warns instead of tiny text | Preview, image dimensions, readable hierarchy, footer |
| Caption/package generation | Facebook package | Instagram package | LinkedIn package | Image, caption, CTA, hashtags, tags, platform metadata |
| Moderation | Safe motivational content | Boundary content requiring rewrite | Unsafe/diagnostic/guaranteed content flagged | Moderation result and no unsafe approval |
| Duplicate controls | Unique quote and template | Near-duplicate theme/CTA warning | Exact duplicate block/warning | Duplicate reason and no silent overwrite |
| Human approval/revision | Draft remains draft | Review panel shows full package | Rejection/revision note path without publish | State, note, audit event, no external call |
| Provider readiness/OAuth | Read-only disconnected/ready status | Expired/unready target message | OAuth initiation safety surface without connection | Status, no token in URL, no mutation |
| Scheduler/publishing safety | Read-only queued/approved policy view | Cooldown/daily-cap policy check | Retry/dead-letter visibility with mocked failure | Policy result, no provider call |
| Analytics/insights | Empty/current metrics view | Content/template breakdown | Feedback/opportunity learning surface | Workspace-scoped metrics, no state mutation |
| Billing/usage/audit | Usage/cost dashboard | Plan/quota boundary display | Audit log for local generation/review | Usage, cost, limits, user/workspace/action trace |

## Content cases to create if confirmation is given

| Case ID | Workspace | Category | Theme | Creative | Status target |
|---|---|---|---|---|---|
| GEN-01 | Love, Truth, Motivational, Pain Quotes | Truth Quotes | “Sach bolna mushkil ho sakta hai, par khud se jhooth jeena aur bhi bhaari hota hai.” | Editorial Split or Quiet Luxury | Unscheduled DRAFT |
| GEN-02 | Love, Truth, Motivational, Pain Quotes | Love Quotes | “Pyaar wahi jo tumhe apna rehne de, badalne par majboor na kare.” | Centered Gallery or Paper Note | Unscheduled DRAFT |
| GEN-03 | Love, Truth, Motivational, Pain Quotes | Motivational Quotes | “Aaj perfect nahi, bas kal se ek step aage badhna hai.” | Type Poster or Brush Frame | Unscheduled DRAFT |
| GEN-04 | Love, Truth, Motivational, Pain Quotes | Pain Quotes | “Dard ko chupana zaroori nahi; dheere dheere sambhalna bhi himmat hai.” | Photo + Quote Panel or Paper Note | Unscheduled DRAFT |
| GEN-05 | Love, Truth, Motivational, Pain Quotes | Truth Quotes | Medium-length truth reflection with alternate palette | Quiet Luxury | Unscheduled DRAFT |
| GEN-06 | Love, Truth, Motivational, Pain Quotes | Motivational Quotes | Short action phrase with one highlighted keyword | Neon Geometry | Unscheduled DRAFT |

The minimum three content cases for the user-requested “three separate creations” are GEN-01, GEN-02, and GEN-03. GEN-04 through GEN-06 cover the remaining quote category and creative variations without publishing.

## Evidence standard

A case is **PASS** only when the live browser or authoritative local API visibly proves the behavior. Source code, bundle strings, or an unverified endpoint alone are not sufficient for browser claims. A case is **PARTIAL** when backend evidence exists but browser proof is unavailable. A case is **FAIL** when the live behavior contradicts the knowledge document or safety contract.

## No-op technical cases

Provider readiness, scheduler, analytics, billing, and audit cases must not create external actions merely to produce evidence. They may inspect existing local records, read-only dashboards, or use mocked/unit/integration validation. Any button that would connect, publish, schedule, send, delete, or submit must not be clicked.

## Final report fields

For every case, record: case ID, module, URL, workspace, action performed, whether a local mutation occurred, image/draft/package IDs if created, browser evidence, expected behavior, actual behavior, status, defect severity, and recommended fix. Existing drafts and assets must not be deleted during this audit.
