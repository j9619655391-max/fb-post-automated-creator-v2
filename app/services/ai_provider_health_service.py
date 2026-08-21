from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content_generation import ContentGenerationJob, GenerationStatus
from app.models.generation_plan import ContentGenerationPlan
from app.services.genai_client import active_provider_and_model


def collect_ai_provider_health(db: Session) -> dict[str, Any]:
    """Return safe provider readiness and recent failure metrics without network calls."""
    try:
        provider, model = active_provider_and_model()
    except ValueError as exc:
        provider = "unknown"
        model = None
        provider_error = str(exc)
    else:
        provider_error = None

    configured = bool(
        settings.gemini_api_key if provider == "gemini" else settings.openrouter_api_key if provider == "openrouter" else None
    )
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=max(1, settings.ai_failure_alert_window_minutes))
    failed_jobs = (
        db.query(ContentGenerationJob)
        .filter(
            ContentGenerationJob.status == GenerationStatus.FAILED,
            ContentGenerationJob.completed_at >= cutoff,
            ContentGenerationJob.provider == provider,
        )
        .count()
    )
    retrying_plans = (
        db.query(ContentGenerationPlan)
        .filter(ContentGenerationPlan.last_retry_at >= cutoff)
        .count()
    )
    latest_failure = (
        db.query(ContentGenerationJob)
        .filter(
            ContentGenerationJob.status == GenerationStatus.FAILED,
            ContentGenerationJob.completed_at >= cutoff,
            ContentGenerationJob.provider == provider,
        )
        .order_by(ContentGenerationJob.completed_at.desc())
        .first()
    )
    threshold = max(1, settings.ai_failure_alert_threshold)
    alert = bool(provider_error or not configured or failed_jobs >= threshold or retrying_plans >= threshold)
    alert_reason = provider_error
    if not alert_reason and not configured:
        alert_reason = "provider_not_configured"
    elif not alert_reason and failed_jobs >= threshold:
        alert_reason = "generation_failures"
    elif not alert_reason and retrying_plans >= threshold:
        alert_reason = "plan_retries"
    return {
        "provider": provider,
        "model": model,
        "configured": configured,
        "fallback_enabled": settings.ai_fallback_enabled,
        "window_minutes": settings.ai_failure_alert_window_minutes,
        "failed_jobs": failed_jobs,
        "retrying_plans": retrying_plans,
        "alert": alert,
        "alert_reason": alert_reason,
        "latest_failure": {
            "job_id": latest_failure.id,
            "provider": latest_failure.provider,
            "model": latest_failure.model,
            "error_code": latest_failure.error_code,
            "completed_at": latest_failure.completed_at.isoformat() if latest_failure.completed_at else None,
        } if latest_failure else None,
        "checked_at": now.isoformat(),
    }
