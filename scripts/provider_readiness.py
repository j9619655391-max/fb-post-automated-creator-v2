"""Validate local or production provider configuration without network calls.

Usage:
    python scripts/provider_readiness.py
    python scripts/provider_readiness.py --strict

The diagnostic never prints secret values and never calls Meta, Instagram,
LinkedIn, or Gemini. It is safe to run before supplying sandbox credentials.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

# Support `python scripts/provider_readiness.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = True


def _configured(value: str | None) -> bool:
    return bool(value and value.strip())


def _callback_check(name: str, value: str | None, expected_path: str) -> Check:
    if not _configured(value):
        return Check(name, False, "missing")
    parsed = urlparse(value or "")
    is_local = parsed.hostname in {"localhost", "127.0.0.1"}
    secure_scheme = parsed.scheme == "https" or is_local
    correct_path = parsed.path.rstrip("/") == expected_path
    if secure_scheme and correct_path:
        return Check(name, True, "configured")
    problems = []
    if not secure_scheme:
        problems.append("use HTTPS outside localhost")
    if not correct_path:
        problems.append(f"path must be {expected_path}")
    return Check(name, False, "; ".join(problems))


def collect_checks() -> list[Check]:
    active_provider = (settings.ai_provider or "gemini").strip().lower()
    if active_provider == "openrouter":
        active_ai_configured = _configured(settings.openrouter_api_key)
        active_ai_detail = "configured" if active_ai_configured else "OPENROUTER_API_KEY is required for the active provider"
    elif active_provider == "gemini":
        active_ai_configured = _configured(settings.gemini_api_key)
        active_ai_detail = "configured" if active_ai_configured else "GEMINI_API_KEY is required for the active provider"
    else:
        active_ai_configured = False
        active_ai_detail = f"unsupported AI_PROVIDER={active_provider}"

    return [

        Check("Meta app credentials", _configured(settings.facebook_app_id) and _configured(settings.facebook_app_secret), "configured" if _configured(settings.facebook_app_id) and _configured(settings.facebook_app_secret) else "FACEBOOK_APP_ID and FACEBOOK_APP_SECRET are required"),
        _callback_check("Meta callback", settings.facebook_redirect_uri, "/api/v1/auth/facebook/callback"),
        Check("LinkedIn app credentials", _configured(settings.linkedin_client_id) and _configured(settings.linkedin_client_secret), "configured" if _configured(settings.linkedin_client_id) and _configured(settings.linkedin_client_secret) else "LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are required"),
        _callback_check("LinkedIn callback", settings.linkedin_redirect_uri, "/api/v1/auth/linkedin/callback"),
        Check("Token encryption key", _configured(settings.token_encryption_key), "configured" if _configured(settings.token_encryption_key) else "TOKEN_ENCRYPTION_KEY is required"),
        Check("Active AI provider", active_ai_configured, active_ai_detail),
        Check("Gemini API key", _configured(settings.gemini_api_key), "configured" if _configured(settings.gemini_api_key) else "not configured", required=False),
        Check("OpenRouter API key", _configured(settings.openrouter_api_key), "configured" if _configured(settings.openrouter_api_key) else "not configured", required=False),

        Check("Database", _configured(settings.database_url), "configured" if _configured(settings.database_url) else "DATABASE_URL is missing"),
        Check("Celery broker", _configured(settings.celery_broker_url), "configured" if _configured(settings.celery_broker_url) else "CELERY_BROKER_URL is missing"),
        Check("Production secret", settings.secret_key != "supersecretkeychangeinproduction", "non-default" if settings.secret_key != "supersecretkeychangeinproduction" else "SECRET_KEY still uses the development default"),
        Check("Debug mode", not settings.debug, "disabled" if not settings.debug else "DEBUG must be false outside local development"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit non-zero when any required check fails")
    args = parser.parse_args()

    checks = collect_checks()
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")

    failures = [check for check in checks if check.required and not check.ok]
    print(f"\n{len(checks) - len(failures)}/{len(checks)} checks passed")
    if failures and args.strict:
        print("Strict readiness validation failed; no provider API calls were made.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
