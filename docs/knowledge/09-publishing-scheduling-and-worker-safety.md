# Publishing, Scheduling, and Worker Safety Study

## Purpose

Publishing is the highest-risk stage because it affects external pages and audiences. The scheduler and worker must execute only explicitly approved targets, enforce cooldowns and daily caps, classify provider failures, and preserve auditability. A generated draft or approved package must never be treated as permission to publish immediately.

## Preconditions

Before an external attempt, the worker must verify content status, organization access, provider readiness, OAuth/token status, platform target, page/account target, scheduled time, cooldown, daily cap, media availability, and idempotency key. Any failed precondition should stop the attempt without calling the provider.

## Policy controls

| Control | Purpose |
|---|---|
| Human approval | Prevent unreviewed content from leaving the system |
| Target binding | Ensure the correct Meta Page or LinkedIn Account is used |
| Cooldown | Prevent accidental bursts and audience fatigue |
| Daily cap | Enforce workspace/provider limits |
| Idempotency | Prevent duplicate provider posts on retries |
| Audit trail | Explain who, what, where, when, and why |
| Dead-letter state | Stop unsafe repeated retries after terminal failure |

## Failure classification

| Failure | Classification | Worker action |
|---|---|---|
| Expired/invalid token | Auth terminal | Mark failed, require re-authentication |
| Permission/page target mismatch | Auth or configuration terminal | Mark failed, surface target details |
| Rate limit/429 | Retryable | Retry with exponential backoff and cap |
| Network timeout/temporary 5xx | Retryable | Retry with bounded backoff |
| Invalid payload/media | Content terminal | Mark failed, require revision |
| Duplicate provider response | Idempotent success or reconcile | Query provider/reference and avoid duplicate |
| Unknown error | Cautious retry then dead-letter | Preserve raw-safe error classification |

## State transitions

A scheduled job begins queued, becomes running, then succeeds, retries, fails, or dead-letters. Retryable errors must not bypass cooldown or daily caps. Terminal errors must not loop forever. A retry action in the UI should create a new auditable attempt or explicitly reopen the job, not silently mutate history.

## Provider isolation

Meta and LinkedIn targets share policy concepts but have different OAuth, media, and API requirements. A unified executor can share safeguards while keeping provider-specific adapters. No real provider connection, OAuth initiation, Telegram send, or external post should occur without an explicit user action and required confirmation.

## Tests

Test cooldown and daily-cap enforcement, target ownership, token failures, 429/network retries with exponential backoff, invalid payload dead-lettering, idempotency, manual versus scheduled parity, retry UI actions, and audit events. All tests should mock provider calls and assert that unsafe paths make zero external calls.
