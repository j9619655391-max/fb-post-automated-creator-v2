# Approval and Human-Feedback Workflow Study

## Purpose

Approval is the control point where the operator decides whether a generated package is acceptable for the brand and audience. It is not the same as moderation, generation, scheduling, or publishing. The workflow must preserve that distinction in both UI and data state.

## State model

| State | Meaning | Allowed next actions |
|---|---|---|
| `DRAFT` | AI or operator-created content awaiting review | Edit, regenerate after confirmation, submit for approval |
| `PENDING_APPROVAL` | Explicitly submitted to human approval channel | Approve, reject with note, request revision |
| `APPROVED` | Human approved the package | Schedule or publish through policy checks |
| `REJECTED` | Human rejected it | Revise, regenerate, archive with audit trail |
| `PUBLISHED` | Provider confirmed external publication | Analytics and audit only |
| `FAILED` | Action failed and requires diagnosis | Retry if safe, re-authenticate, or dead-letter |

Generation must end in `DRAFT`. It must not jump to `PENDING_APPROVAL` simply because the image was rendered. Publishing must never be reachable from a preview button.

## Human review package

The reviewer should see the image at usable size, image headline/body, caption, CTA, hashtags, tags, target platform, workspace name, category, selected template, language policy, source status, moderation flags, duplicate warnings, and factual-grounding notes. The page should make it obvious whether a field came from the workspace profile, user input, AI suggestion, or an external source.

## Feedback loop

A rejection should capture a structured reason and an optional free-text note. Useful reason values include `wrong_category`, `wrong_tone`, `language_quality`, `visual_quality`, `too_similar`, `unsafe`, `unsupported_claim`, `missing_branding`, and `wrong_platform_variant`. A revision request should reuse the note as a constraint for the next draft rather than blindly regenerating the same content.

## Telegram and browser approval

Telegram can be an approval channel, but a Telegram message must identify workspace, content, platform target, image preview, caption, CTA, hashtags, and status. Receiving a Telegram command must be idempotent, authenticated, and auditable. Browser approval and Telegram approval must update the same content state machine; they must not create two divergent approval records.

## Safety boundaries

No external post, schedule, boost, ad, OAuth change, or destructive deletion is implied by approval review. The user must explicitly confirm sensitive provider actions separately. Rejection never deletes an existing approved/published post; it creates a revision path or marks the draft rejected.

## Tests

Test every state transition, invalid transition, duplicate approval command, rejection note persistence, revision creation, image/package visibility, permission isolation by workspace, and the rule that generated drafts remain unpublished. Provider calls should be mocked and audit records asserted.
