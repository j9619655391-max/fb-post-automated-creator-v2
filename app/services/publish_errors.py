from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FailureClassification:
    code: str
    retryable: bool
    message: str


def classify_publish_failure(exc: Any) -> FailureClassification:
    """Classify Meta/LinkedIn-style errors without exposing provider secrets."""
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None) or getattr(exc, "status_code", None)
    text = str(exc).lower()

    if status_code == 429 or any(term in text for term in ("rate limit", "too many requests", "too many calls")):
        return FailureClassification("RATE_LIMIT", True, "Platform rate limit reached")
    if any(term in text for term in ("timeout", "timed out", "connection reset", "connection refused", "network")):
        return FailureClassification("NETWORK_ERROR", True, "Platform network request failed")
    if status_code and int(status_code) >= 500:
        return FailureClassification("PROVIDER_5XX", True, "Platform service temporarily unavailable")
    if any(term in text for term in ("token", "oauth", "expired", "invalid credential", "authentication")):
        return FailureClassification("AUTH_REQUIRED", False, "Platform connection expired or is invalid")
    if any(term in text for term in ("permission", "forbidden", "unauthorized", "access denied")):
        return FailureClassification("PERMISSION_DENIED", False, "Platform permission was denied")
    if any(term in text for term in ("invalid media", "media container", "unsupported", "validation")):
        return FailureClassification("INVALID_CONTENT", False, "Platform rejected the content or media")
    return FailureClassification("UNKNOWN_PROVIDER_ERROR", True, "Platform request failed temporarily")
