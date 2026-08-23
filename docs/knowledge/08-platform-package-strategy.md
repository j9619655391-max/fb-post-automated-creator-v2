# Platform Package Strategy Study

## Purpose

A social post is a package, not only an image. The platform must produce an image variant, caption, CTA, hashtags, tags, target platform, and review status as one traceable package. Each platform should receive adapted copy and composition while preserving the same approved creative brief.

## Package model

| Field | Requirement |
|---|---|
| Image | Platform-sized, readable, branded, and linked to the package |
| Headline/body | Exact image text shown in review |
| Caption | Separate post text, natural for the platform and language mode |
| CTA | Explicit and low-pressure; not automatically invented contact information |
| Hashtags | Relevant, limited, and category-aware |
| Tags | Verified/user-provided handles or communities only |
| Platform | Facebook, Instagram, or LinkedIn |
| Status | Draft/review state, never implicit publish |
| Audit | Workspace, user, timestamp, and generation/package action |

## Platform adaptation

Meta’s official guidance distinguishes 1:1 and 4:5 Feed assets and recommends 9:16 for Stories, Status, and Reels; it also advises placement-specific uploads and crop review [1]. LinkedIn’s official specification recommends a 1.91:1 image such as 1200×627 for custom Page-post images and notes that edge content may be trimmed [2]. The package service should therefore render separate assets from shared content fields instead of resizing one master image.

| Platform | Copy emphasis | Visual emphasis |
|---|---|---|
| Facebook | Relatable caption, community prompt, share CTA | Landscape or portrait card with central safe zone |
| Instagram | Shorter hook, saves/shares, hashtag discipline | Square/4:5 visual with stronger focal type |
| LinkedIn | Clear reflection, professional restraint when relevant | Landscape, reduced decoration, edge-safe footer |

## Caption and hashtag rules

The image should contain the memorable quote; the caption should add context, reflection, or a small action. Do not duplicate the image paragraph in the caption by default. Hashtags should mix category, language, and intent, but avoid stuffing generic tags. Tags should never be hallucinated.

## Review experience

Content Detail and Creative Studio should show every platform card with image, caption, CTA, hashtags, tags, template, category, and status. A reviewer should be able to compare variants side by side and identify whether a change is platform-specific or a shared brief change.

## Tests

Test all three package variants, image URLs, dimensions, metadata preservation, caption normalization, tag handling, workspace isolation, and draft-only status. Test that a package route never publishes or schedules automatically and that provider errors are surfaced without losing the draft audit trail.

## References

[1]: https://www.facebook.com/business/help/103816146375741 "Meta Business Help — Best practices for aspect ratios across placements"
[2]: https://www.linkedin.com/help/linkedin/answer/a563309/image-specifications-for-your-linkedin-pages-and-career-pages "LinkedIn Help — Image specifications for Pages and Career Pages"
