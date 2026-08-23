# Deep Gap Audit: Workspace-Aware Image Post Creation

## Observed user-facing failures

The New Content screenshot shows Aaditech Solution selected in the active-workspace switcher, but the category defaults to `Motivation`. The business objective and category are not coupled, so a fashion-oriented objective can coexist with a generic category. The category selector is global and date/seed driven rather than recommended from the selected workspace's business profile, approved sources, products, services, or existing content history.

The Edit Content screenshot shows generated title/body text but no attached image in the media section and no image in the social preview. This is expected from the current AI generation contract: `GenerateDraftRequest` accepts category and workspace context but has no source-media, image-template, or image-generation fields. `generate_and_persist_draft` creates a `Content` row with `media_id=None`, and the generated `ContentResponse` exposes only a scalar `media_id`; it does not guarantee a nested serialized media object. The frontend already attempts to render `content.media`, but the backend response schema does not declare that nested field.

The current New Content flow therefore produces a text draft only. The separate Creative Studio can compose images and the separate package endpoint can pair images with captions/hashtags/tags, but AI generation does not invoke either path. The two flows are disconnected, which is why a user can click `Generate business draft` and land on an editor with no image post package.

Workspace sources also have a review lifecycle gap. Source creation defaults to `pending`; website refresh explicitly sets refreshed sources back to `pending`; generation reads only active sources with `review_status == approved`; and the workspace intelligence API/UI exposes no approve or reject action. Thus a source can be added and refreshed but never become eligible for source-grounded generation through the visible workflow.

## Current code evidence

| Gap | Current behavior | Required behavior |
|---|---|---|
| Workspace category | `getCategories()` calls a global endpoint; `list_categories()` orders by static `sort_order,name`; `ContentForm` falls back to a generic category when the expected slug is absent | Category catalog and default recommendation must receive `organization_id` and rank business-fit categories for the selected workspace |
| Business taxonomy | Seed contains fashion categories plus legacy Motivation/Tips/Reflection, but no broad service/business taxonomy for Aaditech-like workspaces | Seed a reusable taxonomy: service showcase, case study, educational/how-to, industry insight, client story, offer/booking, company culture, behind the scenes, plus fashion-specific categories |
| Source eligibility | Added/refreshed sources are pending; generation reads approved sources only; no approval transition exists | Operator can review, approve, reject, or keep a source pending; recommendation and generation must expose evidence provenance |
| AI draft image | Generation request has no media/template fields; persistence creates content with `media_id=None` | Generation must either use a selected workspace-owned source image, create a deterministic text-card image when appropriate, or explicitly return an image-required state rather than silently creating text-only content |
| Content response | Backend `ContentResponse` has `media_id` but no nested `media`; route-side URL mutation cannot be relied upon by Pydantic serialization | Response must include a typed nested media payload with URL, MIME type, and dimensions/filename where available |
| Complete post package | Creative Studio and package endpoint are separate from AI draft generation | One generation action must return/persist content, image variant(s), caption, hook, CTA, hashtags, tags/mentions, risk flags, source hints, and platform variants |
| Preview | New Content social preview renders only title/body and an optional manually uploaded media URL; it does not show generated package metadata | Preview must show actual image plus caption, hashtags, tags, CTA, platform selector, and status for the selected workspace |
| Safety | Approval gate exists, but text-only draft can appear complete even though media/post package is absent | Draft should remain approval-required and show explicit missing-asset or source-confirmation flags |
| Workspace persistence | Active workspace ID is persisted and currently appears correct in the live page | Keep this behavior, but pass the selected ID consistently to categories, sources, image assets, generation, and packages |

## Target contract before implementation

`POST /generation/draft` should accept an explicit organization, recommended or operator-selected category, business objective, template family, optional workspace-owned source media ID, image copy fields, and package generation preferences. It should return a draft record that includes a nested image/media payload, source evidence, category recommendation metadata, and platform package previews. If no product image is selected, quote-card or text-first templates may use a deterministic branded background; product-specific templates must not silently invent a product asset.

The visible New Content page should load a workspace-specific category catalog and recommendation. It should auto-select the recommended category after the active workspace is loaded, show why it was recommended, allow manual override with all applicable business categories, and display source approval status. The Generate button should create a complete draft package, not only title/body text.

## Safe implementation boundary

No OAuth, Telegram send, approval submission, scheduled publishing, live social publishing, boosting, paid advertising, or destructive action is part of this repair. All generated assets remain local drafts/previews until the existing human approval gate is deliberately used.
