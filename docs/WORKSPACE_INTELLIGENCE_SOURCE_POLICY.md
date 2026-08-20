# Workspace Intelligence Source Policy

## Verified source boundaries

The workspace intelligence feature may use two source classes: public business information supplied through approved URLs or public provider metadata, and private/owned account data retrieved only after the workspace owner authorizes the relevant official API.

Meta’s Page API exposes business-page metadata such as name, description, category, link, contact details, and connected Instagram/WhatsApp indicators subject to the app’s permissions and public metadata/content access requirements. Page-owned or user-related information requires the appropriate Page permissions and Page access token. Source: https://developers.facebook.com/docs/graph-api/reference/page/

Meta’s Instagram Platform supports professional Business or Creator accounts. Depending on the login path, the Instagram account must be a professional account and may need to be linked to a Facebook Page. The official API can manage owned media and provide permitted account metadata; it is not a general personal-account scraping mechanism. Source: https://developers.facebook.com/documentation/instagram-platform

The WhatsApp Business Platform is an official business API for Cloud API messaging, Business Management API asset management, templates, analytics, and webhooks. It requires a Business Portfolio/WABA and authorized business phone numbers. User opt-in and approved template policies apply to outbound marketing messages. Personal WhatsApp data must not be collected or automated through unofficial tools. Source: https://developers.facebook.com/documentation/business-messaging/whatsapp/about-the-platform

LinkedIn provides approved products for sign-in, sharing, marketing, community management, and authorized business/page data integrations. The platform must use approved OAuth scopes and product access; arbitrary profile/page scraping is out of scope. Source: https://developer.linkedin.com/product-catalog

## Proposed workspace intelligence boundary

Each workspace will own a structured profile containing business name, description, services/products, audience, locations, brand voice, differentiators, approved claims, contact details, website URLs, social URLs, and source records. Every extracted fact will store its source URL/provider, retrieval time, confidence, and review status.

Website ingestion will fetch only user-supplied public URLs, respect robots.txt and rate limits, follow same-domain links within a bounded page/depth budget, and store normalized text plus citations. Provider ingestion will use official APIs and connected accounts only. WhatsApp will initially be represented as an authorized Business account/contact channel and source metadata; outbound messaging requires a separate consent/template workflow and will not be enabled by profile ingestion alone.

AI generation will receive only workspace-approved knowledge, recent source records, and explicit editorial instructions. Generated posts should cite or retain source hints internally, mark stale or low-confidence facts for review, and never invent contact details, offers, credentials, or platform account ownership.
