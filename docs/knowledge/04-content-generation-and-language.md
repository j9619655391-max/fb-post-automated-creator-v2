# Content Generation and Language Study

## Purpose

Content generation turns workspace intelligence and a selected category into a complete, reviewable draft. It must preserve business context, language policy, brand voice, factual boundaries, and image-package requirements. AI output is an assistive draft, not an autonomous publishing decision.

## Input contract

| Input | Source | Required behavior |
|---|---|---|
| Workspace | Active organization and profile | Never generate against an ambiguous workspace |
| Category | User selection or VCE recommendation | Preserve category integrity |
| Language | Workspace preferred languages | For the quote client, natural Roman Hindi/Hinglish + simple English |
| Objective | Business objective and content goal | Must match the category and client type |
| Theme | User-selected or generated theme | Use as a direction, not as an unverified fact |
| Creative | Archetype, quote length, background, platform | Pass through to media composer |
| Sources | Approved workspace website/media/research | Use only when relevant and clearly grounded |
| Safety | Moderation and risk policy | Reject or revise unsafe framing |

## Prompt contract

The prompt should contain explicit machine-readable blocks such as `WORKSPACE_CONTEXT`, `CATEGORY_RULES`, `HINGLISH_MODE`, `CREATIVE_BRIEF`, `FACTUAL_GUARDRAILS`, and `OUTPUT_SCHEMA`. For this workspace, `HINGLISH_MODE: enabled` must require natural Roman Hindi with simple English and prohibit literal, awkward, or unrelated fashion/product copy.

The output schema should include title, image body, caption, CTA, hashtags, tags, category, language mode, risk flags, and optional source references. The image body must be shorter than the caption and suitable for the selected quote archetype. The service should normalize provider output, validate required fields, run moderation and duplicate checks, persist usage, and create the draft only after all required checks pass.

## AI and human boundary

AI may suggest copy, themes, image text, caption structure, and package variants. It may not decide to publish, schedule, send Telegram, connect OAuth, boost an ad, delete content, or replace an existing draft. A generated record remains `DRAFT` until the separate approval workflow changes its state.

## Hinglish quality rubric

| Dimension | Good result | Failure signal |
|---|---|---|
| Naturalness | Sounds like a bilingual human social caption | Word-for-word translation or unnatural mixing |
| Clarity | One clear idea per quote | Multiple unrelated ideas packed together |
| Rhythm | Intentional phrase-level line breaks | Random wrapping or long unbroken paragraph |
| Tone | Respectful, emotionally specific, simple | Generic hype, shame, or forced slang |
| Language consistency | Stable use of tum/aap and Roman Hindi spelling | Switching register or inconsistent spellings |
| Brand fit | Matches workspace voice and category | Fashion/product advice inside quote page |

## Failure handling

Provider errors should be classified separately from validation errors. A provider outage or quota error should not create a partially valid draft. Invalid JSON, missing fields, unsafe content, duplicate content, or unsupported claims should return a clear error and preserve the ability to retry with a new idempotency key. Usage persistence must be idempotent so an error path cannot mask the original failure with a uniqueness error.

## Usage and audit

Every provider call should persist model, provider, input/output token counts when available, estimated cost, organization, job, and completion status. Audit data should connect generation request, user, workspace, category, creative brief, selected template, and final content record. Sensitive credentials must never appear in prompts, logs, reports, or generated captions.

## Tests

Mock the provider and capture prompts. Assert that Hinglish mode, category rules, creative selection, and factual guardrails are present. Test malformed output, quota exhaustion, duplicate content, unsafe content, idempotency, usage persistence, and draft-only status. No generation test should call an external model or publish to a provider.
