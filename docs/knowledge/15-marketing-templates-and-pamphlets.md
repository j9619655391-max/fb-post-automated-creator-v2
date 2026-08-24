# Marketing Templates and Pamphlets: Research-Backed Product Study

## Purpose

This module defines how the FB Post Generation platform should create **marketing creatives and pamphlets that have a business job**, rather than producing generic posters with text placed on a background. A marketing template must connect a workspace, audience, objective, offer or message, proof, visual hierarchy, call to action, brand system, platform or print specification, accessibility, moderation, approval, and measurement.

The module covers social posts and ads, feed and Stories-style creatives, flyers, one-page handouts, bifold and trifold pamphlets, accordion and gate-fold brochures, event leaflets, service menus, product/service explainers, lead-generation handouts, and campaign families. It extends the existing quote-card and creative-template knowledge rather than replacing it. The active quote workspace remains a valid content case, but a quote card is an **engagement/community template**, not a substitute for a product, service, lead, event, or offer template.

> **Core principle:** A template is a reusable communication contract. It defines the audience, objective, attention sequence, copy roles, asset rules, safe areas, platform or print geometry, accessibility requirements, and approval checks before any image or export is created.

## User problem

The current platform can create complete social packages and deterministic quote cards, but marketing output requires more than a headline, image, caption, and CTA. A product or service client needs a coherent campaign unit: a specific audience, a specific outcome, truthful benefits, proof, contact or destination, and variants that remain recognizable across placements. A pamphlet adds physical-production constraints such as folds, panel order, trim, bleed, safe margins, QR usability, and print-proof review.

Without this module, the platform risks four kinds of failure. It can generate **generic content** that does not match the client’s business objective; it can make an attractive but non-actionable visual; it can invent claims, prices, contacts, or product details; and it can export a file that is visually correct on screen but wrong after crop, fold, trim, or printing.

## Audience and jobs-to-be-done

The module should support several operator and audience types. The operator may be a small business owner, consultant, marketer, designer, or approval manager. The final viewer may be a mobile feed user, an event visitor, a local customer holding a handout, a professional evaluating a service, or a person using a screen reader or magnification tool.

| Audience | Job | Template consequence |
|---|---|---|
| New or unfamiliar audience | Understand who the organization is and remember it | Strong identity, one promise, low density, awareness CTA |
| Interested prospect | Understand whether the offer solves a relevant problem | Problem–solution hierarchy, benefits, proof, next step |
| Ready-to-act prospect | Contact, visit, book, sign up, buy, or request information | Prominent single CTA, destination, friction reducer, truthful urgency |
| Existing customer/community | Learn, return, share, attend, or stay connected | Recognition, helpful value, retention CTA, consistent series system |
| Event/local visitor | Find when, where, why, and how to participate | Date/time/location priority, map or QR, large actionable details |
| Print reader | Scan a physical piece quickly and keep it for later | Cover hook, panel sequence, short sections, readable contact block |
| Assistive-technology user | Access the same meaning and action | Alt text, adjacent URL, semantic PDF, contrast, non-color cues |

## Objective-first operating model

The system must ask for or infer a **single primary objective** before selecting a template. Meta’s official objective guidance maps six simplified objectives to business goals: Awareness, Traffic, Engagement, Leads, App promotion, and Sales [2]. The platform does not need to copy Meta’s names exactly, but it should preserve the principle that creative structure follows the intended outcome.

| Objective family | Primary viewer question | Recommended creative promise | CTA examples | Success signals |
|---|---|---|---|---|
| Awareness | “Who is this and why should I remember it?” | Identity, point of view, memorable promise | Learn more, Follow, Discover | Reach, qualified impressions, recall proxy, profile visits |
| Education/authority | “Can this help me understand or decide?” | One useful insight, framework, checklist, or explanation | Read more, Save, Download | Saves, qualified visits, content completion |
| Engagement/community | “Do I relate to this enough to respond or share?” | Emotional resonance, opinion, conversation, quote, story | Comment, Share, Tell us | Comments, shares, saves, meaningful replies |
| Traffic | “Where should I go next?” | Clear reason to visit a destination | Visit website, Explore, See details | Link clicks, landing-page visits, engaged sessions |
| Leads | “Why should I give my details or start a conversation?” | Specific benefit plus low-friction next step | Get quote, Book call, Message us, Sign up | Qualified leads, form completion, response rate |
| Sales/conversion | “Why should I act now?” | Product/service benefit, proof, offer, objection removal | Shop now, Book now, Get started | Purchases, bookings, revenue, qualified conversion rate |
| Event/local action | “When, where, and how do I participate?” | Event value plus logistics | Register, RSVP, Visit us | Registrations, attendance, calls, scans |
| Retention/re-engagement | “Why should I return or continue?” | New value, reminder, update, loyalty benefit | Return, Renew, Refer, View update | Repeat visits, renewals, referrals |

The interface should prevent a user from selecting a “sales” or “lead” template when no verified offer, destination, contact method, or audience exists. If the workspace has only a quote-page profile, it should recommend community, awareness, education, or engagement formats—not product catalogs or invented offers.

## Marketing template archetypes

Archetypes are more useful than a flat list of colors because they describe the communication pattern. Each archetype should own a grid, text roles, asset requirements, copy limits, CTA treatment, and platform variants.

| Archetype | Communication structure | Best use | Required regions | Common failure to prevent |
|---|---|---|---|---|
| Brand story / identity | Brand cue → point of view → memorable promise → soft CTA | Awareness, positioning, founder or community story | Eyebrow, focal statement, supporting image, identity footer | Logo dominates while message disappears |
| Problem–solution | Audience problem → empathetic insight → solution → next step | Services, education, lead generation | Problem hook, solution headline, 2–3 benefits, CTA | Vague “we can help” claim without a concrete benefit |
| Product/service spotlight | Offer → primary benefit → proof/detail → CTA | Product, service, booking, sales | Product/image zone, title, benefit, detail, CTA | Feature list becomes too dense for mobile |
| Feature–benefit comparison | Current state → option or approach → differentiator → CTA | Consideration, sales, consulting | Two or three comparison groups, proof, CTA | False comparison, unsupported superiority, tiny text |
| Testimonial / social proof | Customer voice → context → proof marker → CTA | Trust building, services, local business | Quote, attribution, verified context, CTA | Fabricated testimonial or anonymous proof treated as fact |
| Offer / promotion | Offer → value → conditions → deadline → CTA | Sales, events, limited campaigns | Offer badge, product/service, validity, terms, CTA | Fake scarcity, expired price, unreadable terms |
| Lead-generation card | Problem → valuable promise → three benefits → low-friction CTA | Lead forms, consultation, download | Hook, benefit list, trust cue, form/destination CTA | Asking for contact details without explaining value |
| Event / launch announcement | What → why attend → date/time/place → registration | Event, launch, opening, webinar | Event title, date, location, speaker/product, CTA | Date or location buried in decorative design |
| Educational explainer | Question → answer → 3–5 steps or facts → next resource | Awareness, authority, onboarding | Numbered steps, diagram/image, source note, CTA | Too much text for a single card; missing source or update date |
| Community / quote card | Emotional hook → concise message → share or reflect CTA | Quote workspace, engagement, retention | Quote, attribution/source policy, identity footer, CTA | Treating a quote card as a sales ad or shrinking long copy |
| Local service / contact card | Need → service area → trust cue → contact route | Local services, pamphlets, handouts | Service list, hours/location, phone/URL/QR, CTA | Invented contact details or a QR code without readable fallback |

A campaign should use a **family of related archetypes**, not one duplicated design. For example, a service launch may include a brand-story card for awareness, a problem–solution card for consideration, a testimonial for trust, a lead-generation card for action, and a reminder card for retention. Shared brand tokens preserve recognition while the information hierarchy changes with the objective.

## Pamphlet and flyer archetypes

A pamphlet is not merely a large social image. It is a physical or downloadable information journey. The closed piece must create an entry point, and the opened piece must guide the reader through a deliberate sequence toward an action.

| Print/digital piece | Geometry | Recommended information journey | Best use |
|---|---|---|---|
| One-sided flyer/poster | Single face | Hook → essential value → action/contact | Notice boards, local promotion, event awareness |
| One-page handout | Front or front/back | Summary → benefits/details → contact | Sales leave-behind, consultation summary |
| Bifold | Four panels | Cover → inside explanation → proof/details → back CTA/contact | Compact service/product introduction |
| Trifold | Six panels | Cover → problem/value → benefits/proof → details → action/back panel | General-purpose service, event, local business |
| Accordion fold | Usually six panels | Sequential story, checklist, timeline, or step-by-step journey | Education, process explanation, travel/event information |
| Gate fold | Usually eight panels | Dramatic cover reveal → central promise → supporting proof → action | Premium launch, campaign reveal, high-impact brand story |
| Double parallel / French fold | Usually eight panels | Layered information or mini-booklet sequence | Detailed service explanation, onboarding, program information |
| Service menu/rate card | Modular panels or pages | Category → offer → inclusion/price → conditions → booking | Services, packages, appointments |
| Event program/guide | Folded or booklet | Event identity → agenda → speakers/activities → logistics → follow-up | Conferences, workshops, launches, community events |
| QR lead magnet | Flyer or folded piece | Valuable promise → brief explanation → QR + readable URL → fallback contact | Downloads, forms, booking, digital catalog |

Common fold structures have different panel counts and mechanical requirements. A single fold yields four panels, a tri-fold six, double parallel and double gate folds eight, accordion six, and French fold eight; inner panels in some folds need to be slightly narrower to fit correctly [10]. The editor therefore needs a fold-aware flat canvas and a folded preview, not just a grid of equal rectangles.

## Copy and information architecture

The copy system should use a **single-message rule**: one primary promise per creative face or panel. The operator may provide rich source material, but the generator must select the one thing the viewer should understand and the one action they should take. Meta’s official guidance notes that people scan feeds quickly, recommends concise primary text, and warns that placement and device truncation can occur [1]. LinkedIn similarly publishes practical limits to avoid truncation, including 150 characters for introductory text, 70 for headlines, and 100 for descriptions in its single-image ad guidance [4]. These limits should be treated as placement guidance, not as a universal guarantee.

| Copy role | Marketing creative | Pamphlet |
|---|---|---|
| Eyebrow/context | Category, audience, event type, or “New” cue | Section label, business category, or panel context |
| Hook/headline | One promise or problem statement | Cover headline that remains clear when folded |
| Support | One sentence, proof marker, or key differentiator | Short paragraphs, bullets, steps, inclusions, or FAQs |
| Benefit | Usually 1–3 benefits | 3–5 benefits or a compact service/product list |
| Proof | Verified testimonial, result, credential, source, or data | Attribution, source note, accreditation, case detail |
| Offer/terms | Price, deadline, eligibility, or condition when verified | Full conditions, validity, disclaimers, and fine-print block |
| CTA | One primary action | One primary action plus readable fallback contact |
| Footer | Truthful brand/handle and optional URL | Brand, address/contact, URL, QR alternative, legal note |
| Accessibility text | Alt text and caption equivalent | Accessible PDF text structure, alt text, readable URL, and scan alternative |

The platform should distinguish **image text**, **post caption**, **description**, and **CTA control**. Image text must remain sparse and legible. The caption can carry context, hashtags, tags, source notes, and additional details. A pamphlet can hold more information, but it still needs headings, grouping, whitespace, and a clear reading order. Digital.gov describes plain language as clear, audience-specific content that should be designed and tested for understandability [8]. This supports a workflow where copy is reviewed for audience fit and comprehension rather than judged only by grammar.

For the active quote workspace, the copy contract remains Hinglish: natural Roman Hindi with simple English where useful. The system must not translate mechanically or replace emotional specificity with generic marketing language. For a product or service workspace, language and claims must come from that workspace’s verified profile and approved sources.

## Visual hierarchy and template anatomy

Nielsen Norman Group defines visual hierarchy for web, graphic, and print displays as organizing elements so the eye consumes them in the intended order. It identifies color/contrast, scale, and grouping/proximity as primary mechanisms, recommends limiting unnecessary type and contrast variations, and emphasizes whitespace and grouping [6]. The platform should encode these relationships as named roles rather than allowing every element to compete equally.

A robust template anatomy is:

1. **Context:** a small eyebrow or category cue that tells the viewer what they are seeing.
2. **Primary promise:** the largest and clearest message, limited to one idea.
3. **Visual proof or focal asset:** a product, person, environment, symbol, diagram, or restrained texture that supports the message rather than competing with it.
4. **Benefit/proof group:** a short, grouped explanation or verified evidence.
5. **Action:** one prominent CTA with enough contrast and adequate surrounding space.
6. **Identity and trust footer:** verified logo, workspace name, handle, URL, contact route, or source note, with empty values omitted rather than represented by placeholder separators.

The renderer should use no more than a small number of type roles per template. The existing creative study recommends one display family and one reading family; that rule should continue. Decorative or script faces must not be used for long copy or small metadata. WCAG 2.2 requires at least 4.5:1 contrast for ordinary text and images of text, with 3:1 permitted for large text, and explains that hue alone does not make text readable [5]. The renderer should therefore calculate contrast against the actual background, not rely on palette names such as “rose” or “sunset.”

## Digital placement requirements

A source creative should not simply be cropped into every placement. Meta provides placement-specific creative and text guidance and warns that copy may be truncated across placements and devices [1]. Its Stories guide describes fullscreen vertical image ads, lists a 30 MB maximum file size, 500 px minimum width, and 1% aspect-ratio tolerance, and reinforces concise primary text [3]. Meta search results also expose placement safe-zone guidance for top, bottom, and side interface overlays; these values should be versioned as placement metadata and not hard-coded as timeless truths.

LinkedIn documents reusable image templates with square or vertical layouts, configurable logo, title/subtitle typography, optional three-benefit lead-generation treatment, CTA, and alt text. It recommends 1200×628 for landscape, 1200×1200 for square, and 720×900 for vertical ads, while warning that square and vertical assets may crop when shared organically [4].

| Placement family | Initial output strategy | Layout rule |
|---|---|---|
| Facebook/LinkedIn landscape | Dedicated 1.91:1 or near-landscape variant | Wide text column, shorter footer, no horizontal overflow |
| Instagram/Facebook square | 1:1 variant | More vertical breathing room, centered hierarchy, readable metadata |
| 4:5 feed/vertical ad | Dedicated vertical feed variant | Do not crop landscape; reflow text and asset intentionally |
| Stories/Reels 9:16 | Fullscreen vertical variant | Reserve top/bottom interface safe zones; keep CTA and logo out of overlays |
| WhatsApp or message-led placement | Compact identity and action variant | Prioritize one action, readable contact or deep link, privacy-aware copy |
| LinkedIn organic-share preview | Separate thumbnail check | Validate crop behavior from 3:2 through 16:9 range and retain focal content |

The implementation should keep `platform_variant`, `placement`, `aspect_ratio`, `safe_area`, `copy_budget`, and `version_checked_at` in the template profile. When platform rules change, the profile can be updated without rewriting every template.

## Print-production requirements

Print export needs more geometry than a social PNG. A production-ready pamphlet should carry a target trim size, bleed, safe margin, fold lines, panel order, color/profile expectations, resolution policy, and export format. PrintNinja explains that full-bleed artwork should extend 0.125 inches beyond the trim line, while critical text and graphics should remain at least 0.125 inches inside the trim; it recommends a 0.25-inch inset for uniform borders because small cutting variance can make thin borders visibly uneven [9]. Adobe’s print-bleed lesson is retained as a production reference, but printer-specific requirements must take priority [11].

| Print field | Required behavior |
|---|---|
| Trim size | Final physical size after cutting; selected by paper standard or printer preset |
| Bleed | Artwork extension beyond trim; never a safe location for critical copy |
| Safe margin | Inset region for headlines, body, CTA, logo, QR, phone, URL, and legal text |
| Border-safe margin | Larger inset when a visually uniform border is part of the design |
| Fold lines | Explicit fold geometry and panel sequence; no important copy on a fold unless intentional |
| Panel widths | Support asymmetric inner panels for fold fit where required |
| Front/back orientation | Show closed and opened views, with readable panel numbering in editor only |
| Export | Print PDF preset plus preview PNG; exact color/marks determined by printer profile |
| Proof | Low-resolution screen proof and, where available, a print-proof checklist |
| Version | Store print specification, template version, and export timestamp |

The platform should initially support a small set of common presets such as one-page flyer, A5/A4-style handout, letter-style handout, bifold, and trifold, while allowing custom dimensions. Presets must not hide printer-specific variables. The user should be able to export a screen/digital version separately from a print-production version.

## QR codes, links, and accessibility

QR codes are bridges between physical and digital media, but they can create access barriers. Section 508 guidance recommends describing the purpose of a QR code in alt text, providing an adjacent text link or URL, maintaining strong contrast, avoiding unexpected automatic actions, and testing across devices and assistive technologies [7]. It also notes practical print risks such as small size, poor resolution, lighting, and link staleness.

Therefore every QR block should have:

| QR requirement | Platform behavior |
|---|---|
| Verified destination | Only use a workspace-approved URL or generated campaign URL |
| Purpose label | Store human-readable label such as “Scan to book a consultation” |
| Accessible alternative | Print the short URL or provide adjacent digital hyperlink |
| Contrast and quiet space | Validate code/background contrast and reserve uncluttered space |
| Minimum-size warning | Warn when selected print size or export resolution risks scanning |
| User control | Link to a page with a clear next step rather than an unexpected action |
| Expiry and ownership | Track destination owner, validity, campaign, and update status |
| Test evidence | Record a test result or leave status as unverified; never claim a QR works without a test |

For digital images, the package should carry alt text and a plain-text caption equivalent. For downloadable pamphlet PDFs, the long-term target is a tagged, searchable, reading-order-aware PDF rather than a raster-only sheet. If the current export cannot guarantee semantic accessibility, the UI should state that limitation and require a companion HTML/text version for high-stakes content.

## Sources, claims, moderation, and compliance

Marketing creative is often more claim-sensitive than a quote card. A source may provide a product specification, service description, testimonial, price, date, credential, location, or performance statement. The platform must distinguish **verified workspace facts**, **approved source facts**, **operator-supplied claims pending review**, and **AI-proposed wording**.

The following rules are mandatory:

| Risk | Required control |
|---|---|
| Invented logo, handle, URL, phone, address, price, or service | Omit the field or mark it missing; never fabricate it |
| Unsupported superiority or guaranteed outcome | Flag for rewrite and require evidence or softer wording |
| Expired offer/date/event | Block approval until validity is confirmed |
| Testimonial or review | Require attribution and source status; do not create fake customer voice |
| Health, financial, legal, or sensitive claim | Apply stronger moderation and human review; no diagnosis or guarantee |
| Copyrighted image or copy | Require source/license state or approved upload |
| QR destination | Require verified destination and accessible fallback |
| Fine print | Keep readable, do not hide material conditions in tiny type |
| Multilingual copy | Review language quality, cultural meaning, transliteration, and truncation |
| Repeated creative | Run exact and near-duplicate checks across recent workspace outputs |

Approval is not the same as moderation. A creative can be factually grounded but visually unreadable, or visually strong but unsupported. The system should show separate gates for content safety, claims/source grounding, duplicate/fatigue, language, visual fit, accessibility, and human approval.

## Desired state machine

The proposed state machine applies to both social marketing creatives and pamphlet exports:

```text
BRIEF_CAPTURED
  → OBJECTIVE_MAPPED
  → SOURCES_AND_ASSETS_VERIFIED
  → COPY_DRAFTED
  → MODERATION_AND_CLAIM_CHECKED
  → DUPLICATE_AND_FATIGUE_CHECKED
  → TEMPLATE_SELECTED
  → PREVIEW_RENDERED
  → VISUAL_ACCESSIBILITY_PRINT_QA
  → HUMAN_REVIEW
  → APPROVED
  → EXPORTED_AS_DRAFT
  → (optional, separate) SCHEDULED
  → (optional, separate) PUBLISHED
```

A failure at any gate returns the item to a reviewable state with a reason. For example, `OVERFLOW`, `LOW_CONTRAST`, `MISSING_DESTINATION`, `UNVERIFIED_CLAIM`, `FOLD_COLLISION`, `QR_UNTESTED`, `EXPIRED_OFFER`, or `DUPLICATE_THEME`. Rendering an image or PDF does not imply approval, scheduling, or publication.

## Inputs and outputs

| Input | Example | Verification |
|---|---|---|
| Workspace identity | Name, logo, handle, brand colors, fonts | Workspace-owned and non-empty values only |
| Business objective | Leads, sales, awareness, event, community | Objective selected or explicitly confirmed |
| Audience | Segment, location, language, need | Operator input or approved workspace profile |
| Offer/message | Product, service, lesson, quote, event | Source-grounded and current |
| CTA/destination | URL, form, phone, WhatsApp, RSVP | Verified target, no invented contact data |
| Proof | Testimonial, credential, source, data | Approved source/claim state |
| Media | Image, logo, icon, QR, diagram | Ownership/license/status and safe crop |
| Template | Archetype, fold, platform placement | Compatible with objective and medium |
| Production spec | Size, bleed, folds, color/export profile | Printer or platform profile |
| Language policy | Hinglish, Hindi, English, multilingual | Workspace language rules and review |
| Tracking | Campaign ID, UTM, vanity URL, coupon | Optional but verified and not misleading |

Outputs should include the image/PDF asset, platform-specific image variants, caption or panel copy, CTA, hashtags/tags where relevant, alt text, source/claim references, QR metadata, quality-gate results, approval state, and an audit record. A pamphlet package should additionally include flat artwork, folded-preview render, print specification, and accessible companion text when available.

## Proposed data and API mapping

The current platform already has workspace profiles, brand themes, media, content packages, deterministic image variants, moderation, duplicate checks, approval, and provider safety. The following additions are proposed as contracts, not claims that they already exist.

| Proposed entity/field | Purpose | Existing relationship |
|---|---|---|
| `MarketingBrief` | Objective, audience, funnel stage, message, CTA, destination, validity | Belongs to organization/workspace; feeds content generation |
| `TemplateArchetype` | Named layout, text roles, asset rules, objective compatibility | Extends current template-family model |
| `PlacementProfile` | Platform, placement, aspect ratio, copy budget, safe zones, version | Feeds platform variant rendering |
| `PamphletSpec` | Fold, trim, bleed, panel widths, print preset, export profile | Feeds print renderer/export |
| `ClaimReference` | Claim text, source, approval state, expiry, confidence | Connects workspace intelligence to copy and moderation |
| `QrTarget` | Destination, label, short URL, alt text, test status, expiry | Attaches to creative/pamphlet package |
| `CreativeProof` | Overflow, contrast, crop, fold, QR, readability, asset checks | Visible in preview and approval panel |
| `CampaignFamily` | Shared brief and brand tokens across multiple archetypes/variants | Connects related content drafts |

The UI should expose these through the existing workspace-first surfaces. A practical route set would be `marketing brief`, `template library`, `creative preview`, `pamphlet editor`, `print export`, and `quality/approval review`. Any endpoint that creates a draft or export must remain behind an explicit confirmation gate and must not schedule or publish implicitly.

## Current platform behavior and gaps

The current platform can create deterministic branded text-card variants for Facebook, Instagram, and LinkedIn using fixed sizes of 1200×630, 1080×1080, and 1200×627. It supports quote-card and other template families, six quote background presets, workspace brand colors/fonts, complete package metadata, and draft-only confirmation. The recent browser audit proved package plumbing and safety gates but also found systematic landscape quote overflow/cropping, very small Instagram metadata, and an empty footer marker when contact fields are blank.

The following marketing and pamphlet capabilities are not yet complete:

| Gap | Severity | Required outcome |
|---|---:|---|
| Objective-to-archetype selection | P0 | No generic template chosen without a business job |
| Real marketing archetypes | P0 | Problem–solution, spotlight, proof, offer, lead, event, education, and community families |
| Safe-area and measured text layout | P0 | No crop/overflow; long copy routes to another layout or rewrite |
| Empty-footer normalization | P0 | Omit empty contact segments and placeholders |
| Placement-specific variants | P1 | Feed, square, 4:5, Stories/Reels, and network previews |
| Pamphlet/fold data model | P1 | Fold-aware panels, widths, order, and preview |
| Print export | P1 | Bleed, trim, safe area, fold guides, printer profile, PDF proof |
| QR workflow | P1 | Verified target, label, fallback URL, contrast, size, and test state |
| Claims/source panel | P1 | Show evidence, expiry, and unsupported-claim flags before approval |
| Accessible digital export | P1 | Alt text, companion text, tagged/searchable PDF roadmap |
| Campaign-family variants | P2 | One brief produces coordinated but non-duplicate creative set |
| Outcome analytics | P2 | Objective-specific metrics and template/fatigue learning |

## Quality checklist

A creative or pamphlet should not reach the human approval stage as “ready” unless the following checks are either passed or clearly marked as an operator decision:

| Gate | Pass condition |
|---|---|
| Objective fit | Template and CTA match the selected goal and funnel stage |
| Workspace integrity | Active workspace identity, language, palette, and verified assets are used |
| Claim grounding | Prices, dates, benefits, proof, contacts, and destinations are sourced or operator-approved |
| Copy clarity | One primary promise, audience-appropriate language, no unnecessary filler |
| Hierarchy | Viewer can identify context, promise, proof/benefit, and action in order |
| Text fit | No overflow, overlap, truncation, or unreadable minimum type |
| Contrast | Normal text targets at least 4.5:1 and large text at least 3:1 [5] |
| Crop safety | Logo, headline, CTA, QR, and critical details remain inside platform safe areas |
| Footer truthfulness | Empty fields disappear; no placeholder, invented, or stale details |
| QR safety | Destination verified, purpose labeled, fallback URL present, scan status honest |
| Print safety | Bleed, trim, safe area, fold lines, and panel widths match the selected spec |
| Accessibility | Alt text/companion text and non-color cues are available |
| Duplicate/fatigue | Exact and near-duplicate checks pass or are reviewed |
| Package completeness | Correct image, caption/panel copy, CTA, tags, alt text, and variant metadata exist |
| Approval safety | Item remains draft until an authorized human approves it |

## Measurement and learning

Measurement must follow the objective, and metrics should be treated as evidence for learning rather than as guarantees. For digital creatives, store workspace-scoped results such as impressions/reach, engagement, saves/shares, CTA clicks, landing-page visits, leads, conversations, bookings, purchases, negative feedback, and approval-revision reasons where the provider makes them available. For pamphlets, support campaign IDs, short URLs, QR scans, coupon or code redemptions, calls, form submissions, and distribution context.

Creative-level quality metrics are equally important. Track text-overflow rate, safe-zone failure rate, contrast failure rate, claim-review rate, duplicate/fatigue warnings, average number of revisions before approval, template/archetype usage, and outcomes by objective and placement. A beautiful template that repeatedly fails approval or produces no action should be retired or revised. A high-performing template should not be blindly copied if it increases audience fatigue or violates workspace-specific brand rules.

## Test requirements

The test suite must combine deterministic layout tests, API/integration tests, browser acceptance, and no-op safety checks.

| Test layer | Required cases |
|---|---|
| Objective mapping | Awareness, lead, sales, event, education, community each select compatible archetypes and CTA fields |
| Workspace isolation | Product workspace cannot inherit quote claims; quote workspace cannot receive product offer text without explicit configuration |
| Copy budgets | Meta-style concise overlay, LinkedIn headline/intro limits, and Stories-specific short variant are warned or adapted [1] [3] [4] |
| Layout fit | Short, medium, and long copy stay inside measured safe boxes for all current and new aspect ratios |
| Contrast | Light/dark combinations, gradient backgrounds, image backgrounds, and large/small text meet thresholds [5] |
| Empty data | Missing logo, handle, website, phone, WhatsApp, and location omit fields without placeholder markers |
| Crop safety | Landscape, square, 4:5, and 9:16 previews preserve headline, CTA, logo, and critical details |
| Fold geometry | Bifold, trifold, accordion, gate, and asymmetric inner panels produce correct panel order and no fold collision [10] |
| Print export | Bleed/trim/safe areas, resolution, export metadata, and printer profile are represented; exact printer rules remain configurable [9] [11] |
| QR safety | Verified and unverified targets, fallback URL, contrast, minimum-size warning, and test status behave correctly [7] |
| Claims/moderation | Unsupported price, guarantee, medical/financial claim, fake testimonial, stale event, and copyrighted asset are flagged |
| Duplicate controls | Exact copy, near copy, same image/CTA, and campaign-family variation produce appropriate warnings |
| Package completeness | Every platform variant has the image, caption, CTA, hashtags/tags where applicable, alt text, and draft state |
| Approval safety | Compose/print export confirmation creates only a local draft/export; no publish, schedule, Telegram, or provider call occurs |
| Analytics | Objective and template identifiers persist so results can be compared without mixing workspaces |

### Browser acceptance cases

The first browser pass should use safe local drafts and exports only. It should not connect providers or publish anything.

| Case | Marketing case | Expected browser proof |
|---|---|---|
| MKT-01 | Awareness/brand-story creative for a verified workspace | Objective, archetype, brand tokens, preview, caption, alt text, and draft-only confirmation |
| MKT-02 | Lead-generation problem–solution creative with verified CTA/URL | Benefits, destination, QR/URL fallback, claim panel, mobile variant, and approval guard |
| MKT-03 | Event or offer creative with date/terms | Prominent date/CTA, expiry/terms warning, placement variants, and no unsupported urgency |
| PMP-01 | One-page flyer with short copy and verified URL | Trim/bleed/safe preview, readable hierarchy, accessible companion text |
| PMP-02 | Trifold service or event pamphlet | Six-panel order, folded preview, panel widths, QR fallback, and print export proof |
| PMP-03 | Long-form educational or product pamphlet | Section hierarchy, overflow/fold checks, source notes, tagged-text limitation disclosure, and draft-only export |

## Phased implementation recommendation

**Phase 1 — Strategy and contracts.** Add objective and funnel fields, marketing brief, archetype catalog, placement profiles, pamphlet spec, claim references, and QR target contracts. Extend the UI to show why an archetype is recommended and which required inputs are missing.

**Phase 2 — Marketing renderer.** Implement measured layout primitives, objective-specific archetypes, platform variants, contrast and overflow checks, truthful footer omission, and crop/safe-zone previews. This phase must fix the current landscape crop defect before new template breadth is added.

**Phase 3 — Pamphlet editor and export.** Add flat-sheet panel grids, fold-aware geometry, print presets, bleed/trim/safe zones, folded preview, QR block, print PDF export, and a companion digital/text output. Keep printer-specific settings configurable.

**Phase 4 — Grounding, moderation, and approval.** Connect claims and source references to copy roles, add offer/date/URL validity checks, QR verification states, duplicate/fatigue checks, language review, and a consolidated quality panel. Preserve human approval as the final gate.

**Phase 5 — Campaign families and learning.** Generate coordinated variants across awareness, consideration, conversion, and retention without copy/image duplication. Record objective, archetype, placement, and revision reasons so analytics can compare real outcomes.

## Final recommendation

The platform should not add a large number of decorative templates before fixing its layout engine and objective model. The correct order is **business objective → audience/message → archetype → copy roles → verified assets/claims → measured layout → platform/print variant → accessibility and production QA → human approval**. This sequence directly addresses the user’s concern that a post should look and behave like real marketing collateral rather than a generic text card.

For the active quote workspace, the first useful marketing extension is a **community and awareness campaign family**: quote card, story/lesson card, carousel explainer, community prompt, and profile-growth card. Product, service, lead, offer, and event templates should appear only for workspaces whose verified profile and sources support those jobs. No template should imply a business, offer, contact detail, or result that the workspace has not supplied.

## References

[1]: https://www.facebook.com/business/help/223409425500940 "Meta Business Help — Creative best practices for text in ads"
[2]: https://www.facebook.com/business/help/1438417719786914 "Meta Business Help — Choosing Meta Ads Manager advertising objectives"
[3]: https://www.facebook.com/business/ads-guide/update/image/instagram-story "Meta Ads Guide — Awareness image ad specs on Instagram Stories"
[4]: https://www.linkedin.com/help/lms/answer/a426534/single-image-ads-advertising-specifications?lang=en "LinkedIn Help — Single image ads advertising specifications"
[5]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum "W3C WAI — Understanding WCAG 2.2 contrast minimum"
[6]: https://www.nngroup.com/articles/visual-hierarchy-ux-definition/ "Nielsen Norman Group — Visual Hierarchy in UX"
[7]: https://www.section508.gov/blog/accessibility-bytes/qr-codes/ "U.S. Section 508 — Accessible QR Code Implementation"
[8]: https://digital.gov/guides/plain-language "Digital.gov — Plain language guide series"
[9]: https://printninja.com/file-setup-for-full-bleed-printing/ "PrintNinja — File setup for full-bleed printing"
[10]: https://www.48hourprint.com/brochure-folding-guide.html "48HourPrint — Brochure folding guide"
[11]: https://www.adobe.com/learn/indesign/web/set-print-bleed "Adobe Learn — Set a print bleed in InDesign"
