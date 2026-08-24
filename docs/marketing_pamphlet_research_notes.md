# Marketing Templates and Pamphlets — Research Notes

## Scope

Research target: workspace-aware marketing template and pamphlet generation for social posts, digital campaigns, printable flyers, leaflets, folded brochures, and campaign families. Required outputs should connect business objective, audience, offer, visual hierarchy, copy, CTA, brand system, platform dimensions, print production, accessibility, moderation, approval, and measurable outcomes.

## Initial authoritative findings

### Meta Business — creative text in ads
Source: https://www.facebook.com/business/help/223409425500940

Meta says people scan Feed quickly, especially on mobile. Its guidance recommends keeping primary text to roughly 1–3 lines, communicating the desired action at a glance, and keeping text short to reduce placement/device truncation. The page gives typical recommended limits of 125 characters for primary text, 40 for headline, and 25 for description, while warning that truncation can still vary by placement and device. Meta also describes placement asset customization: copy can be adapted to Facebook, Messenger, Instagram, WhatsApp, and Audience Network placements. This supports separate platform/placement variants rather than one universal creative.

Design implication: the platform should distinguish image text from post caption, maintain a short mobile-first overlay budget, generate placement-specific copy variants, and show truncation/safe-zone warnings before approval.

### W3C WAI WCAG 2.2 — contrast minimum
Source: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum

WCAG 2.2 SC 1.4.3 states that text and images of text should have at least 4.5:1 contrast, with 3:1 allowed for large text; logos/logotypes are exempt. W3C explains that hue alone is not a reliable proxy for readability, and thin or unusual fonts may appear fainter because of antialiasing. The guidance also notes that text rendered into images should meet the contrast requirement when it is intended to be understood as text, and that image text does not scale as well as real text.

Design implication: the renderer must calculate contrast for text over the actual background, avoid thin display fonts for small copy, preserve a strong text-safe region, and provide accessible caption/alt-text equivalents for text-bearing visuals. Brand marks can follow brand rules, but informative copy cannot rely only on hue or low-contrast decoration.

### Nielsen Norman Group — visual hierarchy
Source: https://www.nngroup.com/articles/visual-hierarchy-ux-definition/

NN/g defines visual hierarchy as organizing a 2D display—webpage, graphic, or print—so the eye consumes elements in intended importance order. It identifies color/contrast, scale, and grouping/proximity/common regions as primary mechanisms. Recommendations include limiting colors in uncomplicated designs, avoiding too many contrast variations, not relying only on color, using no more than about three type sizes for clear hierarchy, making the most important element largest, and using whitespace/grouping to show relationships.

Design implication: every template needs an explicit attention sequence such as brand/context → promise or headline → proof/offer → CTA → supporting details. Template schemas should encode hierarchy roles rather than arbitrary text boxes, with constraints on type sizes, contrast levels, grouping, and whitespace.

### Adobe InDesign — print bleed
Source: https://www.adobe.com/learn/indesign/web/set-print-bleed

The official Adobe learning page is available for the print-bleed topic, but the extracted page was dominated by cookie-settings content in this environment and did not yield the full tutorial text. Use it as a production-reference URL, but verify exact bleed values against the selected printer/specification before implementation; do not hard-code a universal value from this page alone.

Design implication: pamphlet export must distinguish trim size, bleed, safe margin, fold lines, crop marks, color profile, resolution, and printer-specific requirements. An export preset should require a target print specification rather than silently assuming one.

## Research questions to resolve next

1. Which marketing template archetypes serve awareness, consideration, conversion, retention, event, product/service, local business, quote/community, and education objectives?
2. How should a pamphlet differ from a social card, flyer, leaflet, trifold, bifold, gatefold, and booklet in information architecture and export?
3. What copy framework should map offer, audience pain/need, proof, benefit, objection handling, urgency, and CTA into constrained regions?
4. What are the correct digital dimensions and platform-specific safe zones for Facebook, Instagram, LinkedIn, WhatsApp, Stories/Reels, and ads, and which values must come from current platform documentation?
5. What accessibility rules should apply to digital images, downloadable PDFs, print text, QR codes, and alternative text?
6. What implementation contracts, moderation rules, duplicate/fatigue checks, approval gates, and visual QA tests are needed in this platform?

## Digital placement and accessibility findings

### Meta Ads Guide — Instagram Stories
Source: https://www.facebook.com/business/ads-guide/update/image/instagram-story

Meta describes Stories image ads as fullscreen vertical placements and lists a 30 MB maximum file size, 500 px minimum width, and 1% aspect-ratio tolerance. The page reinforces the need to design for the immersive vertical placement and to keep primary text concise at 125 characters. The broader Meta placement guidance found in search results also recommends reserving approximately 14% of the top, 35% of the bottom, and 6% on each side for Stories/Reels overlays; exact safe-zone values should be stored as placement metadata and kept current because platform UI can change.

Design implication: stories/reels templates need a dedicated 9:16 composition with top/bottom UI safe zones, not a cropped feed card. The renderer should reject or warn when headline, logo, QR code, or CTA enters overlay zones.

### LinkedIn Help — single image advertising specifications
Source: https://www.linkedin.com/help/lms/answer/a426534/single-image-ads-advertising-specifications?lang=en

LinkedIn documents reusable image templates with square (1:1) or vertical (4:5) layouts, configurable logo, title/subtitle font and color, image, optional three key benefits for lead-generation objectives, and a call-to-action button. It lists recommended landscape 1200×628, square 1200×1200, and vertical 720×900 dimensions; recommends 4:5 for vertical ads, and notes that square and vertical images may be cropped when shared organically. For ad text, LinkedIn recommends keeping introductory text to 150 characters to avoid truncation, headline to 70, and description to 100. It supports image alt text for screen-reader users and recommends 3:2 to 16:9 for thumbnail rendering to minimize cropping.

Design implication: template models should support logo, title, subtitle, benefits, CTA, alt text, and target-specific copy limits. LinkedIn requires both ad and organic-share previews because a visually correct source asset can still crop in downstream surfaces.

## Source URLs retained

- Meta text in ads: https://www.facebook.com/business/help/223409425500940
- Meta Instagram Stories image ads: https://www.facebook.com/business/ads-guide/update/image/instagram-story
- LinkedIn single-image ads: https://www.linkedin.com/help/lms/answer/a426534/single-image-ads-advertising-specifications?lang=en
- W3C WCAG 2.2 contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum
- Nielsen Norman visual hierarchy: https://www.nngroup.com/articles/visual-hierarchy-ux-definition/
- Adobe InDesign print bleed: https://www.adobe.com/learn/indesign/web/set-print-bleed

## Pamphlet accessibility and communication findings

### U.S. Section 508 — accessible QR-code implementation
Source: https://www.section508.gov/blog/accessibility-bytes/qr-codes/

GSA explains that QR codes used in electronic content need an equivalent alternative-text description and a keyboard-equivalent link. The description should communicate the purpose of scanning, not merely say “QR code.” It recommends an adjacent text URL or link so people who cannot scan can access the same destination, sufficient code/background contrast, a clear user-controlled landing page rather than an unexpected automatic action, and testing across devices and assistive technologies. It also notes that print has separate practical risks—small size, poor resolution, poor lighting, and link staleness—even though Section 508 itself does not apply to print media.

Design implication: QR blocks in pamphlet templates must be optional, purpose-labeled, high contrast, tested, and accompanied by a readable short URL or equivalent CTA. The platform should validate destination, provide alt text, reserve quiet space, and warn if the QR is too small or low contrast for the selected print size.

### Digital.gov — plain-language guide series
Source: https://digital.gov/guides/plain-language

Digital.gov states that public content should be clear and easy to understand, written for its specific audience, designed with content structure in mind, and tested for understandability. The guide connects plain writing to audience definition, clear content, content design, and testing.

Design implication: pamphlet copy should not be treated as a decorative text dump. The generator must define audience and desired action first, use short headings and direct benefits, group related information, and run a readability/content review before approval. Hinglish outputs should preserve natural Roman Hindi plus simple English, avoid awkward literal translation, and make the CTA understandable without relying on visual styling alone.

## Print production and fold findings

### PrintNinja — full-bleed file setup
Source: https://printninja.com/file-setup-for-full-bleed-printing/

PrintNinja explains that artwork for full-bleed printing should extend 0.125 inches beyond the trim line to prevent irregular white edges caused by cutting variance. Critical text and important graphics should remain at least 0.125 inches inside the trim line; uniform borders should be farther inside, with the guide recommending 0.25 inches because small cutting variance makes thin borders visibly uneven. The bleed is trimmed away, so it is not a safe location for critical content.

Design implication: export must model separate bleed, trim, safe, and border-safe zones. The preview should show the folded/trimmed result and warn if logo, CTA, phone, URL, legal copy, or QR code enters bleed or fold-risk areas. Exact printer specifications still take precedence.

### 48HourPrint — brochure fold families
Source: https://www.48hourprint.com/brochure-folding-guide.html

The guide identifies common panel structures: single fold produces four panels; tri-fold produces six; double parallel and double gate folds produce eight; accordion produces six; and French fold produces eight. Some folds require narrower inner panels so the folded piece fits correctly. This means the flat artwork cannot be designed as identical independent panels without accounting for fold mechanics and reading order.

Design implication: the pamphlet generator needs explicit fold type, flat-sheet dimensions, panel widths, panel numbers, front/back orientation, fold lines, cover/back-cover roles, and a fold-preview mode. It should sequence content by the closed-piece journey: cover hook → inside explanation/benefits/proof → action/contact panel, while preserving the printer’s inner-panel compensation rules.

### Meta Business Help — text overlays and Safe Zone
Source: https://www.facebook.com/business/help/980593475366490

Meta defines the Safe Zone as the area where important text overlays and logos will not be cropped out or covered by interface elements. It recommends a clean, sufficiently large, contrasting font, avoiding too many messages, and staying inside the Safe Zone. For 9:16 Stories/Reels creatives, the top, bottom, and side edges should be free of key text, logos, and other critical elements. For non-9:16 Instagram Feed placements such as 1:1 or 4:5, the bottom and side edges should be kept clear. Meta also warns that taller-than-9:16 screens may zoom/crop or add background space, so critical content should sit comfortably inside the protected area.

Design implication: store Safe Zone rules by placement and render them visibly in preview. Do not use a single crop for every placement, and keep disclaimers, QR codes, logos, and primary CTAs away from interface-covered edges.
