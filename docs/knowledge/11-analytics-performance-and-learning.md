# Analytics, Performance, and Learning-Loop Study

## Purpose

Analytics should help the workspace learn which content ideas, visual archetypes, language patterns, CTAs, and platform variants work best. It must not pretend that engagement proves psychological benefit, and it must not create hidden personal profiles from comments or reactions.

## Metric layers

| Layer | Example metrics | Decision supported |
|---|---|---|
| Delivery | Reach, impressions, provider status | Was the post actually delivered? |
| Attention | Views, dwell proxies, click-through where available | Did the creative earn attention? |
| Resonance | Saves, shares, comments, reactions | Which ideas or formats connect? |
| Conversion | Approved workspace-specific action | Did the post support the configured objective? |
| Quality | Rewrite rate, moderation flags, duplicate warnings | Where is the generation system weak? |
| Operations | Retry rate, failure rate, approval time | Is the workflow reliable and safe? |

## Learning dimensions

Analytics should segment by category, template archetype, quote-length mode, background family, CTA, platform, and language mode. It should compare controlled variations rather than declare one universal “best” post. For Motivation, compare autonomy/competence/relatedness framing, not only generic engagement.

## Experimentation

Experiments must have a hypothesis, one primary variable, a defined time window, and a stop condition. Examples include comparing Editorial Split versus Centered Gallery for medium-length Truth quotes or comparing `save this` versus `share with someone` CTAs. Avoid changing typography, category, caption, and platform simultaneously because the result cannot be interpreted.

## Privacy and ethics

Engagement is a content signal, not a diagnosis. Do not infer depression, loneliness, trauma, or personality from a comment, save, or share. Keep analytics aggregated by workspace and content package. Store only the data required for performance and audit needs, with clear retention and deletion controls.

## Feedback integration

Human rejection notes, rewrite reasons, and template selections are high-value learning signals. The system should aggregate them into prompt and template improvements, while retaining the original audit trail. A high rejection rate may indicate wrong category mapping, weak language quality, poor visual readability, or missing workspace context.

## Tests

Test metric ingestion, provider-to-package mapping, workspace isolation, platform segmentation, duplicate metric handling, aggregation windows, error handling, and the rule that analytics cannot change approval or publishing state.
