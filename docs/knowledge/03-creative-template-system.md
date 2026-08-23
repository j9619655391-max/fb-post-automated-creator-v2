# Creative Template and Image System Study

## Purpose

The creative system converts a content brief into a branded image composition. It must produce a readable visual, not merely place text on a background. A template is a reusable composition contract containing layers, grid, type roles, safe areas, asset rules, copy limits, and platform variants.

## Template contract

| Field | Meaning |
|---|---|
| `archetype` | Editorial Split, Centered Gallery, Type Poster, Paper Note, Brush Frame, Photo + Quote Panel, Quiet Luxury, or Neon Geometry |
| `quote_length_mode` | Short, medium, long, or over-limit |
| `layout_grid` | Relative columns, margins, alignment, and vertical zones |
| `type_roles` | Eyebrow, quote, support, CTA, footer |
| `background` | Approved color/photo/texture source and contrast treatment |
| `brand_tokens` | Logo, handle, palette, footer, and typography from workspace profile |
| `platform_variant` | Facebook, Instagram, LinkedIn, and future 9:16 layouts |
| `safe_area` | Protected region for quote and branding away from crop/UI edges |
| `quality_checks` | Contrast, overflow, spelling, logo legibility, and output dimensions |

## Layer model

The renderer should paint background, contrast protection, brand geometry, eyebrow, quote mark, quote body, support line, CTA, and footer as separate layers. This makes it possible to change composition without changing copy and to preserve branding across variations. A long quote should trigger a different layout or a rewrite warning; it should never be compressed into unreadable type.

## Typography system

Each workspace should define one display family and one reading family. The display family is reserved for short focal copy, while the reading family serves quote body, support line, CTA, and footer. Hierarchy should come from size, weight, leading, tracking, and case rather than excessive color or many fonts. Decorative/script fonts must not be used for long body text or small metadata.

## Branding rules

The logo and handle are workspace-owned assets. If they are missing, the renderer may use the verified workspace name as a truthful fallback. It must never invent a handle, URL, phone number, or contact CTA. The footer is a fixed safe region, and busy backgrounds receive a backing plate or tint before small text is drawn.

## Platform variants

Meta guidance distinguishes 1:1, 4:5, and 9:16 placements and recommends placement-specific assets plus crop review [1]. LinkedIn recommends 1.91:1, such as 1200×627, and warns about edge trimming [2]. The platform should use one content model but render separate compositions: square/portrait variants can give the quote more vertical space, while landscape variants use a wider text column and shorter footer.

## Quality gates

| Gate | Pass condition |
|---|---|
| Text fit | No overflow, overlap, or line that becomes illegible |
| Contrast | Normal-sized copy meets a 4.5:1 target; large type meets at least 3:1 [3] |
| Hierarchy | Quote is clearly dominant; footer is secondary but readable |
| Brand | Only approved workspace identity appears |
| Cropping | Important quote, logo, and CTA remain inside safe area |
| Language | Hinglish/Roman Hindi spelling and punctuation reviewed |
| Package | Image URL and matching platform copy are connected |

## Implementation gaps

The current deterministic renderer has quote-card support and background presets, but the next master version should promote archetype and quote-length mode to first-class fields. Creative Studio should show preview-only sample cards before generation, explain why a template is recommended, and let the operator select an alternative. The final render should be gated by explicit confirmation.

## References

[1]: https://www.facebook.com/business/help/103816146375741 "Meta Business Help — Best practices for aspect ratios across placements"
[2]: https://www.linkedin.com/help/linkedin/answer/a563309/image-specifications-for-your-linkedin-pages-and-career-pages "LinkedIn Help — Image specifications for Pages and Career Pages"
[3]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum "W3C WAI — Contrast (Minimum), WCAG 2.2"
