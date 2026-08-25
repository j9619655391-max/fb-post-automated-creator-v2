# Moderation and Duplicate-Control Study

## Purpose

Moderation protects people, brands, and the platform from unsafe, misleading, abusive, or low-quality content. Duplicate control protects the audience from repetitive posts and protects the workspace from template fatigue. These are separate systems: a post can be safe but repetitive, or original but unsafe.

## Gate model

| Gate | Question | Result |
|---|---|---|
| Language | Does the copy follow the workspace language policy? | Pass, revise, or fail |
| Brand/category | Does it belong to the active workspace and selected category? | Pass, warn, or fail |
| Safety | Does it avoid harmful or coercive framing? | Pass, flag, or fail |
| Factual grounding | Are claims and contacts verified? | Pass, source-needed, or fail |
| Duplicate | Is the text or visual pattern too similar to recent content? | Pass, warn, or fail |
| Visual quality | Is the image readable, correctly sized, and branded? | Pass or fail |
| Human approval | Has the operator approved the final package? | Separate final gate |

## Motivation and quote safety taxonomy

The system should flag coercive shame, guaranteed outcomes, burnout glorification, mental-health diagnosis, self-harm romanticization, targeted harassment, unsupported science claims, and invented expertise. Love content should avoid possessiveness and manipulation; Truth content should avoid targeted accusations; Pain content should acknowledge difficulty without glamorizing suffering.

A moderation flag should explain the reason and offer a rewrite direction. It should not silently alter sensitive content. The operator must be able to understand whether the issue is safety, brand fit, language, factual grounding, or duplication.

## Duplicate strategy

Exact duplicates compare normalized title, body, caption, CTA, and hashtags. Near-duplicate checks compare semantic similarity and structural fingerprints such as repeated opening phrase, same CTA, same category, same archetype, same accent treatment, and same emotional pillar. A warning is preferable to a hard block for close ideas when the page’s identity depends on recurring themes.

| Repetition signal | Action |
|---|---|
| Exact text match | Block generation or require meaningful revision |
| Same quote with punctuation changes | Block or require rewrite |
| Same emotional idea in a short window | Warn and suggest a different angle |
| Same template three or more times | Recommend another archetype |
| Same CTA repeatedly | Rotate CTA library |
| Same category streak | Recommend category balance |

## Review ordering

Moderation should run before media composition when it can prevent wasted rendering, then again after final image/package creation for visual and text integrity. A failed quality check must not mark the content as approved. A moderation pass must not bypass human approval.

## Data and privacy

Store only the flags, reasons, and relevant content identifiers needed for auditability. Do not store psychological diagnoses, inferred mental states, or sensitive audience profiles. Engagement data can inform content performance but must not be interpreted as a person’s clinical condition.

## Tests

Tests should cover unsafe motivation phrases, category mismatch, invented contacts, exact duplicates, near-duplicates, CTA fatigue, visual-template repetition, and false-positive review. All moderation tests must use deterministic fixtures and must not call external services.
