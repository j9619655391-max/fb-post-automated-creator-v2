# Quote Creative System Specification

## Product rule

The platform must never create a quote-card image or AI draft merely because a workspace was selected or a category recommendation loaded. The operator first reviews the creative brief, chooses a background template, and explicitly confirms generation. The confirmation must state that the action will create one unscheduled draft package for review and will not publish, schedule, boost, send to Telegram, connect OAuth, or submit for approval.

## Background template families

| Preset | Visual direction | Best fit | Text treatment |
|---|---|---|---|
| `midnight-aurora` | Deep navy-to-black gradient with soft indigo and pink glow shapes | Truth and reflective quotes | Warm gold eyebrow, ivory quote, pink border |
| `warm-paper` | Cream paper field with terracotta brush edge and subtle grain | Love and healing quotes | Charcoal serif quote, terracotta accent, compact footer |
| `rose-editorial` | Plum background with asymmetric rose panel and fine rules | Love and emotional quotes | High-contrast ivory serif, rose highlight, editorial label |
| `sunset-glow` | Coral, saffron, and plum diagonal gradient with translucent circles | Motivational quotes | Dark ink quote on a light central panel, bold CTA chip |
| `minimal-ink` | Off-white field with black typography, one accent line, generous whitespace | Truth and premium minimalist quotes | Large dark serif quote, small uppercase category label |
| `neon-night` | Charcoal field with electric cyan/pink corner geometry | High-energy motivational quotes | Sans-serif quote, highlighted keyword capsule, bright footer |

Each preset must render independently at the three existing platform sizes: Facebook 1200×630, Instagram 1080×1080, and LinkedIn 1200×627. The visual system must reserve a bottom footer safe area, keep the quote inside a bounded text column, and reduce quote font size only when wrapping requires it. It must never squeeze a long quote into a single unreadable line.

## Typography hierarchy

The renderer uses a three-level hierarchy: a small category or theme eyebrow, a large readable quote body, and a compact CTA/footer. The quote body is the focal element and must use at least 6% of canvas width as its starting size for quote cards, with line spacing and horizontal margins that preserve readability at social-feed preview scale. The footer must never overlap the quote or CTA. When a logo or handle is absent, only the verified workspace name may appear as fallback branding.

## UI workflow

The New Content page continues to load recommendations and themes without creating images. The `Generate business draft` action becomes `Review & confirm generation`. A confirmation panel shows the selected workspace, category, objective, quote template, background preset, language mode, and the exact safety statement. Only `Confirm & generate one draft` invokes the AI generation endpoint. Cancel closes the panel without creating a draft or media.

Creative Studio exposes the same preset selector as visual cards with a generated local preview of the selected layout. It also provides a `Use branded quote text-card background` option when no source image is selected. The compose button remains disabled until the operator has checked `I reviewed this creative brief` and clicks the explicit confirm action. Existing source-backed composition remains available and uses the selected background preset as the overlay style.

## Acceptance tests

A test must prove that opening New Content and changing category, objective, or background preset does not call the generation endpoint. A second test must prove that only the explicit confirmation action triggers the request. Backend tests must validate all six presets, all three platform dimensions, readable non-empty output, and package metadata preservation for caption, CTA, hashtags, tags, and draft status. A safety regression must prove that no route in this flow changes status to pending approval or posts externally.
