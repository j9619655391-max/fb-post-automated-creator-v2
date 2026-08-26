from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.content_category import ContentCategory
from app.models.generation_plan import (

    ApprovalMode,
    ContentGenerationPlan,
    GenerationPlanStatus,
    GenerationRecurrence,
)
from app.services.content_generation_service import GenerationProviderError, generate_and_persist_draft

from app.services.content_service import ContentService
from app.services.risk_policy_service import assess_content_risk, autopilot_decision, get_or_create_policy


logger = logging.getLogger(__name__)





def _ensure_access(db: Session, plan: ContentGenerationPlan, user_id: int) -> None:
    if plan.created_by_id == user_id:
        return
    if plan.organization_id:
        ContentService(db)._verify_org_access(user_id, plan.organization_id)
        return
    raise ValueError("User does not have access to this generation plan")


def _resolve_plan_category(db: Session, data) -> tuple[int | None, str | None]:
    """Normalize workspace plans to the curated category catalog.

    Legacy global plans may still carry a free-text category for compatibility.
    Workspace plans must resolve to a category row so manual and autopilot flows
    cannot drift into unrelated labels such as Motivation.
    """
    if data.category_id is not None:
        category = db.query(ContentCategory).filter(ContentCategory.id == data.category_id).first()
        if category is None:
            raise ValueError("Selected business category was not found")
        return category.id, category.name
    if data.organization_id:
        requested = (data.category_name or "").strip().casefold()
        if requested:
            category = (
                db.query(ContentCategory)
                .filter(ContentCategory.name.ilike(requested) | ContentCategory.slug.ilike(requested))
                .first()
            )
            if category:
                return category.id, category.name
        raise ValueError("Select a category from the selected workspace catalog")
    return None, (data.category_name or "").strip() or None


def create_plan(db: Session, user_id: int, data) -> ContentGenerationPlan:
    if data.organization_id:
        ContentService(db)._verify_org_access(user_id, data.organization_id)
    category_id, category_name = _resolve_plan_category(db, data)
    next_run = data.next_run_at
    if not next_run.tzinfo:
        next_run = next_run.replace(tzinfo=timezone.utc)
    if next_run <= datetime.now(timezone.utc):
        raise ValueError("The first plan run must be in the future")

    plan = ContentGenerationPlan(
        organization_id=data.organization_id,
        created_by_id=user_id,
        name=data.name,
        category_id=category_id,
        category_name=category_name,
        extra_instruction=data.extra_instruction,
        recurrence=data.recurrence,
        approval_mode=data.approval_mode,
        status=GenerationPlanStatus.ACTIVE,
        active=True,
        next_run_at=next_run,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def list_plans(db: Session, user_id: int) -> List[ContentGenerationPlan]:
    from sqlalchemy import or_
    from app.models.organization import OrganizationMember

    organization_ids = [
        row[0]
        for row in db.query(OrganizationMember.organization_id)
        .filter(OrganizationMember.user_id == user_id)
        .all()
    ]
    query = db.query(ContentGenerationPlan).filter(
        or_(
            ContentGenerationPlan.created_by_id == user_id,
            ContentGenerationPlan.organization_id.in_(organization_ids or [-1]),
        )
    )
    return query.order_by(ContentGenerationPlan.next_run_at).all()


def get_plan(db: Session, plan_id: int, user_id: int) -> Optional[ContentGenerationPlan]:
    plan = db.query(ContentGenerationPlan).filter(ContentGenerationPlan.id == plan_id).first()
    if not plan:
        return None
    _ensure_access(db, plan, user_id)
    return plan


def set_plan_status(db: Session, plan_id: int, user_id: int, status: GenerationPlanStatus) -> ContentGenerationPlan:
    plan = get_plan(db, plan_id, user_id)
    if not plan:
        raise ValueError("Generation plan not found")
    plan.status = status
    plan.active = status == GenerationPlanStatus.ACTIVE
    db.commit()
    db.refresh(plan)
    return plan


def _advance_plan(plan: ContentGenerationPlan, run_at: datetime) -> None:
    plan.last_run_at = run_at
    interval = timedelta(days=7 if plan.recurrence == GenerationRecurrence.WEEKLY else 1)
    next_run = plan.next_run_at
    if not next_run.tzinfo:
        next_run = next_run.replace(tzinfo=timezone.utc)
    if not run_at.tzinfo:
        run_at = run_at.replace(tzinfo=timezone.utc)
    while next_run <= run_at:

        next_run += interval
    plan.next_run_at = next_run


def run_plan(db: Session, plan: ContentGenerationPlan) -> ContentGenerationPlan:
    """Run one due plan occurrence and advance its cursor after a durable result."""
    if plan.status != GenerationPlanStatus.ACTIVE or not plan.active:
        return plan
    if plan.organization_id:
        if not plan.category_id:
            raise ValueError("Workspace automation plan requires a curated business category before it can run")
        policy = get_or_create_policy(db, plan.organization_id)
        if policy.emergency_stop:
            raise ValueError("Workspace emergency stop is active")
        start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        generated_today = (
            db.query(Content)
            .filter(
                Content.organization_id == plan.organization_id,
                Content.generated_by_ai.is_(True),
                Content.created_at >= start_of_day,
            )
            .count()
        )
        if generated_today >= policy.max_daily_generated_drafts:
            raise ValueError("Workspace daily generated-draft cap reached")
    run_at = plan.next_run_at

    idempotency_key = f"generation-plan:{plan.id}:{run_at.isoformat()}"
    job = generate_and_persist_draft(

        db,
        plan.created_by_id,
        category_id=plan.category_id,
        category_name=plan.category_name,
        extra_instruction=plan.extra_instruction,
        organization_id=plan.organization_id,
        idempotency_key=idempotency_key,
    )
    if plan.organization_id and getattr(job, "content", None) is not None:
        assess_content_risk(job.content)
        # Controlled mode only grants a policy decision; it never bypasses the
        # approval-required status or directly invokes a social publisher.
        autopilot_decision(db, plan.organization_id, job.content)
        db.flush()
    plan.failure_count = 0

    plan.last_provider = None
    plan.last_error_code = None
    plan.last_error_message = None
    plan.last_retry_at = None
    _advance_plan(plan, run_at)
    db.commit()

    db.refresh(plan)
    return plan


def _reschedule_failed_plan(db: Session, plan_id: int, now: datetime, exc: Exception) -> bool:
    """Move failed plans forward so provider failures do not cause a hot loop."""
    plan = db.query(ContentGenerationPlan).filter(ContentGenerationPlan.id == plan_id).first()
    if not plan:
        return False
    plan.failure_count = (plan.failure_count or 0) + 1
    plan.last_provider = getattr(exc, "provider", None)
    plan.last_error_code = "PROVIDER_RETRY" if isinstance(exc, GenerationProviderError) and exc.retryable else "GENERATION_FAILED"
    plan.last_error_message = str(exc)[:1000]
    plan.last_retry_at = now
    if isinstance(exc, GenerationProviderError) and exc.retryable:
        delay = min(3600, max(300, exc.retry_after_seconds or 900))
        plan.next_run_at = now + timedelta(seconds=delay)
        logger.warning(
            "generation_plan.provider_retry",
            extra={
                "plan_id": plan.id,
                "provider": exc.provider or "unknown",
                "retry_delay_seconds": delay,
            },
        )
        return True
    _advance_plan(plan, now)
    logger.error(
        "generation_plan.failed_until_next_occurrence",
        extra={"plan_id": plan.id, "error_type": type(exc).__name__},
    )
    return False


def run_due_plans(db: Session, now: Optional[datetime] = None) -> dict:
    now = now or datetime.now(timezone.utc)

    due = (
        db.query(ContentGenerationPlan)
        .filter(
            ContentGenerationPlan.status == GenerationPlanStatus.ACTIVE,
            ContentGenerationPlan.active.is_(True),
            ContentGenerationPlan.next_run_at <= now,
        )
        .order_by(ContentGenerationPlan.next_run_at)
        .all()
    )
    generated = 0
    failed = 0
    retry_scheduled = 0
    for plan in due:
        try:
            run_plan(db, plan)
            generated += 1
        except Exception as exc:
            db.rollback()
            if _reschedule_failed_plan(db, plan.id, now, exc):
                retry_scheduled += 1
            failed += 1
            db.commit()
    return {
        "generated": generated,
        "failed": failed,
        "retry_scheduled": retry_scheduled,
        "due": len(due),
    }
