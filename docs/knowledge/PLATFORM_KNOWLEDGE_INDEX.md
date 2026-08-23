# FB Post Generation Platform Knowledge Library

## Purpose

This library is the platform’s durable product and engineering knowledge base. It records the reasoning, operating rules, research findings, safety boundaries, content strategies, and implementation contracts that should guide future generation, moderation, review, publishing, analytics, and workspace decisions. It is not a one-off task note and it must be updated when a module’s behavior changes.

## Module map

| Module | Knowledge document | Primary product surface | Primary implementation areas |
|---|---|---|---|
| Motivation | `01-motivation-module-case-study.md` | Motivation category, New Content, Creative Studio | `content_generation_service.py`, VCE categories, quote-card renderer |
| Love / Truth / Pain quote strategy | `02-quote-category-strategy.md` | Quote workspace categories and recommendations | `vce_service.py`, workspace bootstrap, prompt rules |
| Creative templates and image system | `03-creative-template-system.md` | Creative Studio and generated media | `media_composer_service.py`, brand themes, media routes |
| Hinglish content generation | `04-content-generation-and-language.md` | New Content and AI draft generation | generation routes, prompt construction, usage records |
| Moderation and duplicate checks | `05-moderation-and-duplicate-controls.md` | Draft safety and quality gates | `content_moderation_service.py`, risk policy, content APIs |
| Human approval and feedback loop | `06-approval-and-feedback-workflow.md` | Content Detail, approval actions, revision notes | content routes, Telegram approval service, revisions |
| Workspace intelligence and sources | `07-workspace-intelligence-and-source-grounding.md` | Workspace Knowledge | workspace intelligence service, VCE, source/media approval |
| Platform packages and variants | `08-platform-package-strategy.md` | Facebook, Instagram, LinkedIn package review | content package service, package routes, media variants |
| Publishing and scheduling safety | `09-publishing-scheduling-and-worker-safety.md` | Scheduler, Autopilot, Production | scheduler services, policy, failure classification |
| OAuth and provider readiness | `10-provider-oauth-and-readiness.md` | Platforms and provider setup | Meta/LinkedIn OAuth, sandbox readiness, account sync |
| Analytics and learning loop | `11-analytics-performance-and-learning.md` | Analytics and Insights | performance service, publishing metrics, opportunities |
| Billing and AI usage | `12-usage-cost-and-plan-controls.md` | Billing | billing service, generation usage, plan limits |
| End-to-end architecture | `13-end-to-end-content-creator-operating-model.md` | Cross-module | all major routes/services/models |
| Research and social listening | `14-research-opportunities-and-social-listening.md` | Insights/opportunities | opportunity service, social listening, recommendations |

## Shared invariants

The platform must preserve these invariants across all modules:

1. **Workspace-first context:** every recommendation, creative, source, caption, and metric must be tied to the active organization/workspace.
2. **Business/category integrity:** a quote workspace must not receive unrelated product or fashion guidance; product clients must not receive generic motivational content unless explicitly configured.
3. **Human approval by default:** generation creates a draft for review. It does not publish, schedule, boost, send to Telegram, connect OAuth, or submit for approval without the correct explicit action and confirmation.
4. **Truthful grounding:** logos, handles, URLs, phone numbers, claims, prices, product details, and sources must come from verified workspace inputs or clearly marked research; the system must not invent them.
5. **Image plus copy:** a complete post package includes a readable image, caption, CTA, hashtags, tags, and platform-specific variants.
6. **Language policy:** the workspace’s preferred language and tone must be enforced in prompts, validation, captions, image text, and revisions.
7. **Quality gates:** moderation, duplicate checks, contrast/readability checks, factual-grounding flags, and approval state are separate gates; passing one does not imply passing all.
8. **No destructive convenience:** existing drafts, source assets, workspace data, and provider connections are not deleted or replaced without explicit confirmation.
9. **Auditability:** important mutations and publish attempts must be traceable to a user, workspace, action, status transition, and timestamp.
10. **Provider isolation:** external publishing is disabled or sandboxed until provider readiness, OAuth state, page/account target, cooldown, and daily cap policies all pass.

## Study-document standard

Every module document must contain: module purpose, user problem, target audience, key concepts and research, current platform behavior, desired operating model, inputs and outputs, state machine, failure cases, safety rules, quality checklist, metrics, API/UI/data mapping, implementation gaps, test requirements, and references. Research-backed claims must use inline numbered citations and a References section.

## Update policy

When a module changes, update its study document, this index if the scope changes, and the project-level instructions only for durable cross-task rules. Do not store temporary browser results, credentials, one-off draft IDs, or unapproved creative choices as permanent knowledge.
