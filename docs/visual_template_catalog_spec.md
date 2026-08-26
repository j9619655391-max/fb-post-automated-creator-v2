# Visual Template Catalog and Category Card Design Specification

**Status:** Audit and design baseline before implementation  
**Author:** Manus AI  
**Scope:** Image-first social posts for every workspace category, with Facebook, Instagram, and LinkedIn variants, human approval, truthful source-grounded content, and no external publishing by default.

## 1. Executive finding

The current product does not yet have a true visual template catalog. The New Content page exposes six broad labels—fashion editorial, service/editorial, product/software catalog, technology explainer, case study/solution story, and quote card—with descriptions, but it does not show actual visual cards. A user cannot see where the photo, screenshot, logo, headline, benefit, proof, CTA, or footer will appear before generating. The current selector is therefore a **family selector**, not a category-specific card chooser.

The backend has a comparatively rich category taxonomy and workspace-signal ranking, but the visual contract is flattened into six family values. The older VCE service still returns text hook templates with `{hook}`, `{body}`, and `{cta}` substitution; it does not return visual layout metadata. The API schema has no stable card ID, preview asset, slot definitions, asset requirements, typography roles, safe-zone data, or category compatibility list. The renderer has six layout families, but several unrelated categories are routed through the same generic composition.

This explains the screenshots: the form changes family names and background theme cards, but there is no visual card deck representing the selected category. The correct fix is not merely to add more dropdown options. The product needs a versioned **category-aware visual card catalog** shared by the UI preview, AI brief, renderer, package metadata, QA, and approval record.

## 2. Research principles

The design system follows the following evidence-backed principles.

First, one visual should communicate one primary job. Adobe Express recommends a hierarchy of headline or main message, supporting detail, brand/context, and CTA, while keeping the image text short and putting the full explanation in the caption [1]. Canva's visual-hierarchy guidance emphasizes focal point, size, contrast, typographic levels, spacing, and composition [2].

Second, imagery must be intentional. Tubik distinguishes graphics, photos, quotes, screenshots, and data visualizations as different content types and recommends matching visual material to the business goal and platform [3]. A software product post should therefore not be rendered as a generic fashion-like gradient with text; it needs a verified UI screenshot, product mockup, architecture cue, or service image.

Third, category and funnel stage must influence composition. Fashion strategy guidance describes Instagram as a digital lookbook and emphasizes editorial campaign photography, lifestyle imagery, styling inspiration, UGC, seasonal collections, and behind-the-scenes storytelling [4]. Case-study references recommend a focused message, precise evidence, a challenge-to-result narrative, and visually clear metrics or screenshots [5] [6].

Fourth, visual identity and approval are part of the card, not an afterthought. Brand guidelines recommend a defined objective, audience, approval workflow, consistent identity, correct dimensions, tailored platform messaging, and permission-aware reuse of user-generated content [7]. Every logo, photo, testimonial, metric, URL, and claim must carry provenance or an explicit unavailable state.

Fifth, readability must be measurable. WCAG 2.2 requires at least 4.5:1 contrast for normal text and 3:1 for large text [8]. The image renderer must test contrast on the actual background and reject or revise cards that cannot support a readable text treatment. LinkedIn documents horizontal 1.91:1, square 1:1, and mobile vertical formats, with 1200×628 recommended for horizontal and 1200×1200 for square [9]. Instagram preserves images up to 1080px wide only within a supported aspect-ratio range and crops unsupported ratios [10]. Meta documents placement-specific specifications and safe-zone considerations [11].

## 3. Target product model

The product should separate the following concepts, because they currently collapse into one selector.

| Concept | Meaning | Example |
|---|---|---|
| Business category | What the workspace actually does | Custom software development |
| Content objective | What this post should achieve | Education, proof, inquiry, product discovery |
| Card archetype | The communication pattern | Feature spotlight, workflow explainer, client result |
| Card variant | A concrete visual composition | Split-screen UI feature, three-step workflow, metric proof |
| Platform variant | Export geometry and platform adaptations | Facebook landscape, Instagram square, LinkedIn landscape |
| Asset slot | A required or optional input location | Logo, hero image, screenshot, metric, CTA, footer |
| Copy role | What text is allowed in a slot | Eyebrow, headline, detail, proof, CTA, attribution |
| Evidence state | Whether the content is verified | Verified, workspace-provided, AI suggestion, unavailable |
| QA state | Whether the rendered artifact is safe | Structural pass, contrast pass, crop pass, approval required |

A selectable item in the UI should therefore be a card object, not a family string. Every card object should include at least:

```text
id
version
name
family
category_slugs[]
objective_slugs[]
description
thumbnail_url_or_inline_preview
hero_treatment
slots[]
required_assets[]
optional_assets[]
copy_budgets
font_roles
color_roles
safe_zones_by_platform
cta_policy
provenance_policy
alt_text_pattern
qa_rules
```

The preview thumbnail must be generated from the same layout definition as the production renderer. It must show representative placeholder labels for logo, image, headline, proof, CTA, and footer, so a user can understand the final composition before confirming generation. It must never be a decorative background-only swatch pretending to be a complete card.

## 4. Card catalog by category

The catalog should begin with a useful set of concrete cards. A single category can map to multiple cards; a card can support several closely related categories, but the compatibility must be explicit and ranked.

### 4.1 IT products and technology solutions

This umbrella category includes IT products, software, infrastructure, consulting, and managed technology services. It must not inherit fashion or motivational visual logic.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `it-feature-spotlight` | Feature spotlight | Large product or interface image on one side; branded text panel on the other; one capability highlighted | Verified product screenshot or workspace media; logo; optional feature icon | Eyebrow: product/category; headline: one benefit; detail: one sentence; CTA: Request demo / Learn more only when configured |
| `it-workflow-explainer` | Workflow in three steps | Numbered 1–2–3 flow with connectors and a small product/service visual | Verified workflow facts, icons, optional screenshot, logo | Headline: workflow promise; three short step labels; CTA: See how it works |
| `it-integration-map` | Integration map | Central system with 2–4 connected systems or APIs; restrained technical grid | Verified integration names/logos only when supplied; diagram icons; logo | Headline: integration outcome; labels for systems; CTA: Discuss integration |
| `it-security-checklist` | Security checklist | Dark technical panel with 3–4 check items and shield/security visual | Verified security controls only; security icon; logo | Headline: risk or protection theme; checklist labels; no unsupported compliance claim; CTA: Talk to security team |
| `it-cloud-infrastructure` | Cloud architecture | Simplified architecture diagram with input, services, and output zones | Verified architecture/source facts; cloud provider marks only if used; logo | Headline: infrastructure outcome; 2–3 labels; CTA: Plan your cloud setup |
| `it-product-ui-tour` | Product UI tour | Device/browser mockup occupying the hero area with two callout pins | Verified UI screenshot; product name; logo | Headline: what the user can do; max two callouts; CTA: Explore the product |
| `it-service-capability` | Service capability | People/process or abstract infrastructure visual with capability chips | Workspace media or branded fallback; verified service list; logo | Headline: service promise; 2–3 capability chips; CTA: Book consultation |
| `it-case-result` | Technology case result | Before/after or metric-led result card with project/client context | Approved case-study evidence; chart or screenshot; client logo only if approved | One verified metric or qualitative outcome; source label; CTA: Read the case |
| `it-qa-testing` | Quality assurance | Test matrix/checklist with device/browser icons and a product visual | Verified test facts; screenshot or test illustration; logo | Headline: quality outcome; 3 concise checks; CTA: Get a QA review |
| `it-training-enablement` | Technical training | Instructor/learner or lesson visual plus a three-topic strip | Approved training/workshop imagery; topic labels; logo | Headline: skill/outcome; audience label; CTA: View training |

Unsupported claims such as “100% secure,” “guaranteed uptime,” or fabricated client metrics must not be populated automatically. If evidence is missing, the card should show a neutral capability statement or require operator editing.

### 4.2 Fashion, tailoring, boutique, and apparel

Fashion cards need the product or person to be the focal point. Generic quote layouts are not acceptable for a product or collection post.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `fashion-product-hero` | Product hero | Full-bleed or split product/model image with a restrained text block | Approved product/model photo; logo; optional fabric detail | Collection/product name, one descriptor, price only if supplied; CTA: Shop / Enquire |
| `fashion-lookbook` | Lookbook pair | Two or three coordinated editorial images with collection label | Approved campaign imagery; logo; collection name | Short collection statement; occasion/season label; CTA: View collection |
| `fashion-style-guide` | Styling guide | Main outfit image plus 2–3 small accessory/detail callouts | Approved product images; icon/callout labels; logo | “How to style…” headline; short tips; CTA: Ask a stylist |
| `fashion-fabric-craft` | Craft and fabric detail | Macro fabric/embroidery image with material and craftsmanship callouts | Approved macro/product image; verified material facts; logo | Craft/process headline; 2–3 facts; CTA: Discover craftsmanship |
| `fashion-bridal-occasion` | Bridal or occasion edit | Hero model/product image with an occasion ribbon and appointment panel | Approved occasion imagery; appointment/contact details if configured; logo | Occasion headline; service or collection detail; CTA: Book appointment |
| `fashion-ugc-proof` | Customer styling proof | Customer image or testimonial card with explicit permission/provenance | Permissioned UGC; customer name/handle only if approved; logo | Short verified quote or styling note; CTA: Share your look |
| `fashion-seasonal-drop` | Seasonal drop | Bold seasonal color treatment, one hero product, launch date only if configured | Approved product/campaign image; seasonal palette; logo | Drop name, verified date/availability; CTA: Explore the drop |

The renderer should preserve image quality, avoid placing text over the garment's face or important silhouette, and use whitespace rather than adding multiple decorative badges.

### 4.3 Education, training, coaching, and enablement

Education cards should teach, clarify, or invite a learner. They should use diagrams, checklists, or instructor/learner imagery rather than generic motivational gradients.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `education-quick-tip` | One quick tip | Numbered tip with supporting illustration or classroom image | Verified educational image/illustration; logo | One lesson headline; one actionable line; CTA: Save this tip |
| `education-checklist` | Learning checklist | Three to five checklist rows with a small subject visual | Topic icons/illustration; logo | Headline; concise checklist; CTA: Get the full guide |
| `education-concept-map` | Concept map | Central concept with connected subtopics | Verified concept labels; diagram icons; logo | One concept headline; 3–4 labels; CTA: Learn more |
| `education-course-card` | Course or workshop | Instructor/student image with course title and audience strip | Approved instructor/course image; date only if supplied; logo | Course promise; target audience; CTA: Enrol / Register only when configured |
| `education-explainer` | Explainer visual | Before/after, process, or simple diagram composition | Verified facts, diagram elements, logo | Question-led headline; short answer; CTA: Read the explanation |
| `education-student-proof` | Learner outcome | Learner image or approved testimonial with one verified outcome | Permissioned testimonial; learner identity state; logo | Short quote/outcome; no fabricated result; CTA: Explore learner stories |
| `education-event` | Class or webinar announcement | Event image, title, date/time panel, and registration CTA | Event details; speaker image only if supplied; logo | Event title and exact details; CTA: Register / Attend |

### 4.4 Service, consulting, agency, local business, and managed support

Service cards should make the service concrete through process, outcome, people, or proof. They should not rely on abstract “we are the best” copy.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `service-problem-solution` | Problem to solution | Left problem state, right solution state, connected by a simple transition | Workspace media or safe branded illustration; logo | Pain-point headline; one solution benefit; CTA: Book consultation |
| `service-capability-grid` | Capability grid | Hero service image with three capability chips | Workspace media; verified service list; logo | One promise plus three capabilities; CTA: Explore services |
| `service-process` | How we work | Three-step process timeline with team/process visual | Verified process facts; team image if supplied; logo | Step labels; CTA: Start a conversation |
| `service-local-offer` | Local offer | Product/service image, location/service label, offer panel | Offer asset and exact terms; location; logo | Offer only when verified; expiry/eligibility required for urgency; CTA: Enquire |
| `service-testimonial` | Client voice | Client quote with service visual or portrait and provenance badge | Permissioned testimonial; client identity state; logo | Short quote; no invented attribution; CTA: See how we help |
| `service-faq` | FAQ answer | Question as headline, answer block, supporting icon/photo | Verified source answer; logo | One question and concise answer; CTA: Ask us |

### 4.5 Product, e-commerce, and retail beyond fashion

Product cards must visually show the item, use case, or comparison. Prices, discounts, stock, and dates are never invented.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `product-hero` | Product hero | Product cutout or contextual photo with clear name and benefit panel | Approved product image; logo; optional price | Product name and one benefit; CTA: View product |
| `product-benefit-stack` | Benefit stack | Product image plus three verified benefit rows | Product image; benefit facts; logo | Short headline; three benefits; CTA: Learn more |
| `product-comparison` | Comparison card | Two or three product variants in aligned columns | Product images and verified attributes; logo | Comparison labels; no unsupported superlatives; CTA: Compare options |
| `product-how-to-use` | Use case | Product in context with numbered usage steps | Product/lifestyle image; steps; logo | One use case; 2–3 steps; CTA: Try it |
| `product-offer` | Offer card | Product hero, offer band, terms footer, CTA safe zone | Product image; exact offer terms; logo | Offer/date/eligibility required; CTA: Claim offer only when valid |

### 4.6 Quotes, community, reflection, and Hinglish quote pages

Quote cards are a distinct content type, not a fallback for every business. The quote is the visual focal point; branding is supportive.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `quote-editorial` | Editorial quote | Large quote mark, high-contrast quote, small attribution area, logo/footer | Branded background or approved portrait; logo | Quote text; attribution only if verified; CTA: Share if it resonates |
| `quote-photo-overlay` | Photo quote | Full-bleed approved photo with controlled overlay panel | Permissioned/approved photo; logo | Short quote; no dense body; CTA: Save this thought |
| `quote-conversation` | Conversation quote | Two speech-panel layout for a short Hinglish exchange | Branded illustration or approved image; logo | Two short lines; no fabricated speakers; CTA: Tag someone |
| `quote-series` | Series marker | Strong series label, quote, episode/date only when configured | Background preset; logo/handle | Quote plus series identity; CTA: Follow for more |

Attribution must never be fabricated. If the quote is original to the workspace, the card should say “Original thought by [workspace]” only when that attribution is configured.

### 4.7 News, research, industry insight, and data content

These cards are especially important for a static website or low-change business: the source and publication date must be visible in metadata/caption, and no external trend should be treated as a workspace fact without review.

| Card ID | Card name | Visual composition | Image/graphic slots | Copy and CTA contract |
|---|---|---|---|---|
| `insight-stat` | One-stat insight | Large statistic with source/date footer and supporting visual | Verified metric/chart; source label; logo | One stat and interpretation; CTA: Read the insight |
| `insight-trend` | Trend snapshot | Trend headline plus three signal chips or mini-chart | Verified research/chart; source/date; logo | Trend statement; source required; CTA: Explore the trend |
| `insight-explainer` | Industry explainer | Diagram or concept visual with a concise explanation | Source-grounded diagram; logo | Question and answer; CTA: Learn what changed |
| `news-summary` | News summary | Source masthead area, headline, relevant image, date line | Licensed/approved image or fallback illustration; source link | Exact headline or adapted summary; source/provenance required; CTA: Read more |

## 5. Shared visual anatomy

Every card should use a predictable hierarchy but allow category-specific composition.

| Layer | Purpose | Required behavior |
|---|---|---|
| Brand/context | Identify workspace or series | Logo/wordmark/handle in a reserved, non-competing slot; use name/URL when logo is absent |
| Eyebrow | Orient the viewer | Category, series, feature, collection, or source label; short and optional |
| Focal visual | Stop the scroll | Approved image, screenshot, product cutout, diagram, portrait, or branded illustration according to card type |
| Headline | State the one main idea | Largest text role; short, high-contrast, fitted within safe box |
| Supporting detail | Explain benefit or context | One sentence, 2–3 chips, or 2–4 labeled steps depending on card |
| Proof | Establish credibility | Metric, testimonial, source, or evidence only when verified; otherwise omit rather than invent |
| CTA | Make the next action clear | One short truthful action, separate from footer and outside crop risk |
| Footer | Supply identity/contact/source | Handle, URL, location, source, or disclaimer; low hierarchy but readable |

The renderer must model these as named rectangles or layout regions. No text is allowed to draw into another region. A card fails QA if a required slot cannot fit without violating its copy budget, safe zone, contrast, or minimum readable size.

## 6. Asset and provenance policy

A card must declare which asset is used in each visual slot. Workspace-provided photos, screenshots, logos, and documents are preferred. AI-generated decorative backgrounds may be used only when clearly marked as generated and when they do not imply real photography. A deterministic gradient or geometric fallback must be labeled internally as a branded fallback, not described as real photography.

The package must retain provenance for every image and informative visual. Suggested states are `workspace_upload`, `workspace_source`, `approved_ugc`, `licensed_stock`, `ai_generated`, `branded_fallback`, and `not_available`. `not_available` cannot satisfy a card that requires a real product, client, student, or event image.

The AI may suggest a card and copy, but it cannot create a client logo, testimonial, metric, certification, discount, stock status, event date, or source attribution. Missing evidence should produce a visible “needs evidence” state and block approval when the card requires it.

## 7. Platform variants and safe zones

The initial production exports remain Facebook 1200×630, Instagram 1080×1080, and LinkedIn 1200×627. The catalog must store geometry independently for each platform, even when the card ID is shared. The product should later add Instagram 1080×1350 and dedicated 9:16 Story/Reel cards rather than silently cropping feed designs.

The platform preview should show the export at realistic feed scale. Critical elements—headline, logo, CTA, proof, QR code, contact number, and source—must remain inside an inner safe rectangle. Platform-specific crop previews must be separate from the source canvas. The card definition should include at least:

```text
platform
width
height
safe_margin_left
safe_margin_top
safe_margin_right
safe_margin_bottom
ui_exclusion_zones
min_font_size
max_text_lines
```

Meta and Instagram requirements can change, so dimensions and placement rules must be versioned and updateable rather than scattered as hard-coded UI assumptions [9] [10] [11].

## 8. UI requirements for New Content and Creative Studio

The current dropdown should be replaced or supplemented by a visual card browser. After workspace, category, objective, and language are selected, the UI should show a grid of cards filtered by category/objective compatibility. Each card must display a visual preview, name, supported category labels, intended use, asset requirement badge, and the hierarchy of its slots. Selecting a card must update the structured `card_id`; changing category must clear incompatible cards and themes immediately.

A selected card detail panel should show:

1. A thumbnail or deterministic preview with placeholder logo, image, headline, proof, CTA, and footer areas.
2. “Best for” explanation such as product discovery, lead generation, education, proof, or community.
3. Required assets, with exact states such as “workspace screenshot required” or “branded fallback allowed.”
4. Short image-text limits separated from the full caption.
5. Platform tabs for Facebook, Instagram, and LinkedIn previews.
6. Evidence/provenance warnings before the confirmation gate.
7. A clear statement that no image or draft is created until the user explicitly confirms.

The UI should not display six generic backgrounds and call them templates. Background themes can remain a secondary styling choice only after a concrete card is selected.

## 9. QA and acceptance criteria

A card catalog implementation is not complete until all of the following are true.

| Acceptance area | Required result |
|---|---|
| Catalog completeness | Every active category has at least three compatible visual cards, and each card has a stable ID/version and visible preview. |
| Category truthfulness | IT, fashion, education, quotes, services, products, and insight cards use visibly different visual logic and asset requirements. |
| Slot fidelity | Preview slots and production renderer slots match; logo, image, headline, detail/proof, CTA, and footer are explicit. |
| Copy safety | Long headline/body/CTA/footer values are wrapped or truncated within named boxes; no overlap, clipping, or overflow is possible. |
| Asset safety | Required image/logo/evidence gaps are visible and approval-blocking where appropriate; no fabricated claim is inserted. |
| Readability | Contrast is checked against the actual background; normal text targets at least 4.5:1 and large text at least 3:1 [8]. |
| Platform safety | All three current exports are rendered and crop-previewed independently; critical elements remain inside safe zones. |
| Provenance | Each informative visual has a provenance state and alt-text pattern; UGC requires permission/attribution. |
| Approval safety | Selecting a card or previewing it does not create a draft, media asset, schedule, or external action. Generation remains behind explicit confirmation. |
| Regression coverage | Tests cover every card family, every platform size, missing assets, pathological copy, contrast failure, incompatible category selection, and stale async theme responses. |
| Browser evidence | Read-only browser audit confirms category filtering, visible card previews, card selection, platform preview tabs, and confirmation gate without publishing or scheduling. |

## 10. Recommended implementation order

The implementation should proceed in controlled slices.

First, add a backend catalog module with typed card definitions and a read-only endpoint returning category/objective-compatible cards. Do not delete the existing family values until migration compatibility is established.

Second, add a `card_id` and structured card metadata to the compose request/response, while preserving `template_family` as a derived compatibility field. The AI generation brief should select a card based on category and objective, not choose a generic family directly.

Third, create deterministic preview rendering from the same card definitions. The preview should use placeholders and never consume AI or external image quota. This directly addresses the screenshots without mutating content.

Fourth, update New Content and Creative Studio to show the visual card browser, required asset states, platform tabs, and separate image text/caption controls. Incompatible selections and stale themes must be cleared immediately.

Fifth, adapt the production renderer family by family. The existing six families can remain implementation primitives temporarily, but each concrete card must own its slot geometry and visual treatment. The renderer should return layout QA metadata such as `text_fit`, `copy_truncated`, `safe_area_pass`, `contrast_pass`, `asset_slots_pass`, and `collision_pass`.

Sixth, add deterministic tests and read-only browser checks. Only after the UI and renderer pass should a local draft/image-package generation be considered, and it requires explicit confirmation because it creates persistent media/draft state.

## 11. Current audit disposition

| Finding | Disposition |
|---|---|
| Six text-only family selectors instead of visual cards | **P0 product/design gap; requires catalog and preview implementation.** |
| Category-specific business logic exists in taxonomy but not in visual selection | **P0 contract gap; card IDs and compatibility mapping required.** |
| VCE hook templates remain text substitution | **P1 legacy path; must not be used as the visual-card contract.** |
| Background theme tiles are not full card previews | **P1 UX gap; retain as secondary styling only.** |
| Existing renderer safe-zone fix | **PASS for the tested family-level renderer, but not sufficient for category-card completeness.** |
| Existing legacy `/content/23` visual output | **Historical FAIL/P0 remains until explicitly regenerated; do not overwrite automatically.** |
| External publishing and scheduling | **Not tested or mutated in this audit; approval and authorization rules remain in force.** |

## References

[1]: https://www.adobe.com/express/learn/blog/design-tips-for-social-media-graphics "Adobe Express — A beginner’s guide to social media graphics"

[2]: https://www.canva.com/learn/visual-hierarchy/ "Canva — The ultimate guide to visual hierarchy"

[3]: https://tubikstudio.com/blog/social-media-graphics-design-tips-and-best-practices/ "Tubik Studio — Social Media Graphics: Design Tips and Best Practices"

[4]: https://emplifi.io/resources/social-media-strategy-for-fashion/ "Emplifi — A complete guide to creating a social media strategy for fashion brands"

[5]: https://visme.co/blog/case-study-template/ "Visme — How to Create a Case Study + 14 Case Study Templates"

[6]: https://www.adobe.com/express/learn/blog/marketing-case-study "Adobe Express — Marketing case study 101"

[7]: https://brand.ucsb.edu/social-media/best-practices "UC Santa Barbara Brand Guidelines — Social Media Best Practices"

[8]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum "W3C WAI — Understanding WCAG 2.2 Success Criterion 1.4.3"

[9]: https://business.linkedin.com/advertise/ads/sponsored-content/single-image-ads-specs "LinkedIn — Single Image Ads Specifications"

[10]: https://help.instagram.com/1631821640426723/ "Instagram Help Center — Image resolution of photos you share on Instagram"

[11]: https://www.facebook.com/business/ads-guide/update "Meta — Facebook Ads Guide: Ad format specs and recommendations"
