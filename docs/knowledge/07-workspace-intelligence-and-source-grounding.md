# Workspace Intelligence and Source-Grounding Study

## Purpose

Workspace Intelligence is the context layer that tells the platform who the client is, what the business/page does, which languages and tones are allowed, which categories matter, and which sources are trustworthy. Without it, generation falls back to generic content and the platform can recommend the wrong objective or template.

## Knowledge sources

| Source | What it contributes | Trust rule |
|---|---|---|
| Workspace profile | Description, industry, languages, voice, palette, contacts | Primary client-controlled context |
| Category catalog | Structured content taxonomy | Used for routing and validation |
| Website/social URLs | Public brand and offer signals | Pending until reviewed; never treated as verified automatically |
| Uploaded media | Logos, product/background assets | Must belong to active workspace |
| Research/social signals | Trends and external context | Must be labeled and grounded before factual use |
| Recent content | Repetition and performance context | Used for fatigue control, not private profiling |

## Approval of sources

A source can be discovered, pending, approved, rejected, or stale. PENDING does not mean verified. The system must show source status and evidence used in category recommendation. It must not turn a website URL into factual claims or image content until the operator approves it or the configured verification policy passes.

## Recommendation logic

The recommendation engine should rank categories using workspace name, description, industry, preferred languages, source summaries, and recent history. Evidence should be visible as short terms or signals. A quote workspace should rank Love, Truth, Motivational, and Pain categories above product/fashion categories; a fashion client should receive product/editorial categories instead.

## Workspace isolation

Every profile, source, media asset, category preference, content record, package, metric, and audit event must be scoped to the organization. Users may access only organizations they belong to. A selected media asset from another workspace must be rejected at the API boundary.

## Missing-data behavior

The system should not fill blanks with invented URLs, phone numbers, handles, logos, or product facts. When data is absent, the UI should say what is missing and allow a truthful fallback such as the workspace name. Missing data may lower confidence or require review, but should not silently become hallucinated content.

## UI contract

Workspace Knowledge should expose profile, language, voice, palette, brand assets, URLs, source statuses, categories, and approval controls. New Content and Creative Studio should show the active workspace name and explain which profile signals drove the recommendation.

## Tests

Test organization isolation, blank optional URLs, profile save/load, source pending/approved behavior, category evidence, media ownership, recommendation mismatch, and prevention of invented contacts. Include a regression test where a quote workspace cannot receive fashion/product guidance.
