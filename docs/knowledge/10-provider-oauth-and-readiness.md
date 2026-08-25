# Provider OAuth and Readiness Study

## Purpose

Provider integration connects the local platform to real social accounts. It must be treated as a security and readiness module, not as a button that makes publishing automatically available.

## Secure OAuth lifecycle

OAuth initiation must use a short-lived, one-time, server-side state value tied to the current user, organization, provider, redirect intent, and expiry. Do not place JWTs or long-lived credentials in URL query parameters. On callback, validate state, expiry, one-time use, provider, redirect intent, and authenticated user before exchanging the authorization code. Tokens must be encrypted at rest and never printed in logs, reports, prompts, or browser-visible URLs.

## Readiness checklist

| Check | Pass condition |
|---|---|
| Provider configuration | App credentials and redirect URI are configured safely |
| OAuth state | Short-lived, one-time state validates successfully |
| Account/page target | User selected a real permitted page/account |
| Permissions | Required scopes granted and verified |
| Token health | Token is present, unexpired, and provider-readable |
| Media support | Image format, size, and URL are provider-compatible |
| Policy | Cooldown, daily cap, approval, and audit checks pass |
| Failure recovery | Re-authenticate and retry paths are visible |

## Meta and LinkedIn separation

Meta Pages and LinkedIn Accounts should use provider-specific adapters and target models even if the scheduler exposes one unified execution interface. Page IDs, account IDs, permissions, token behavior, media upload flow, and error codes must not be assumed interchangeable.

## UI behavior

Platforms should clearly show disconnected, pending, ready, expired, permission-limited, and failed states. A `Connect` action must not imply approval to publish. A failed provider job should offer `Re-authenticate` or `Retry` only when the failure classification permits it.

## Tests

Test state issuance, replay prevention, expiry, wrong-provider rejection, wrong-user rejection, redirect-intent validation, encrypted token storage, target isolation, expired-token UI, and zero external calls on unready targets.
