# Provider Sandbox Readiness Findings

**Date:** 2026-08-21

## Local deployment audit

The local Windows Docker deployment is running PostgreSQL, Redis, FastAPI, Celery Worker, and Celery Beat. The active AI provider is OpenRouter with model `openrouter/free`; both Gemini and OpenRouter credentials are configured in the ignored server-side `.env`. The safe readiness diagnostic makes no provider API calls and reports 6/12 checks passed.

The remaining local readiness failures are expected until provider sandbox credentials are supplied: Meta app credentials, Meta HTTPS/local callback configuration, LinkedIn app credentials, LinkedIn callback configuration, token-encryption key, and a non-default production `SECRET_KEY`. Debug mode is disabled, the database is configured, and the Celery broker is configured.

## Official publishing prerequisites

### Facebook Pages

Meta’s current Pages API documentation says Page publishing uses a Page access token obtained through user authentication. The documented publishing permissions include `pages_manage_posts`; Page engagement and moderation require additional permissions such as `pages_read_engagement` and `pages_manage_engagement`. The app user must have the relevant Page tasks. Page posts are created through `POST /{page-id}/feed`; Meta’s documentation also states scheduled publish times must be between 10 minutes and 30 days from the request when using the API’s scheduled-publish mode.[1] [2]

### Instagram professional accounts

Meta’s current Instagram Content Publishing documentation requires an Instagram professional account and a connected authorization path. With Facebook Login, the documented permissions include `instagram_basic`, `instagram_content_publish`, and `pages_read_engagement`; media containers are created at `/<IG_ID>/media` and published with `/<IG_ID>/media_publish`. Media URLs must be publicly accessible when Meta fetches them. Meta documents a 100 API-published-post limit in a moving 24-hour period for Instagram accounts and recommends that applications enforce their own publishing limits.[3]

### LinkedIn organization pages

LinkedIn’s current Posts API requires versioned REST headers and `X-Restli-Protocol-Version: 2.0.0`. Organization posting requires `w_organization_social` and an authenticated member with an eligible organization role such as `ADMINISTRATOR`, `DIRECT_SPONSORED_CONTENT_POSTER`, or `CONTENT_ADMIN`. Text posts are created with `POST https://api.linkedin.com/rest/posts` and a 201 response returns the post ID in `x-restli-id`. LinkedIn also warns that the Marketing Version 202508 is scheduled to sunset on August 17, 2026, so production configuration must target the current supported version rather than the sunset version.[4]

## Next implementation implications

The next safe engineering step is to add non-invasive provider health checks that validate configuration and authorized target metadata without publishing. Real publishing should remain blocked until the user supplies valid Meta and LinkedIn developer credentials, secure callback URLs, authorized sandbox targets, and required permissions. Instagram validation should include professional-account linkage, public media hosting, container status handling, and the application-side rate limit.

## References

[1]: https://developers.facebook.com/documentation/pages-api "Meta: Facebook Pages API"
[2]: https://developers.facebook.com/documentation/pages-api/posts "Meta: Pages API Posts"
[3]: https://developers.facebook.com/documentation/instagram-platform/content-publishing "Meta: Instagram Content Publishing"
[4]: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07 "Microsoft Learn: LinkedIn Posts API"
