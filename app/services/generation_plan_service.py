from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.generation_plan import (
    ApprovalMode,
    ContentGenerationPlan,
    GenerationPlanStatus,
    GenerationRecurrence,
)
from app.services.content_generation_service import generate_and_persist_draft
from app.services.content_service import ContentService


def _ensure_access(db: Session, plan: ContentGenerationPlan, user_id: int) -> None:
    if plan.created_by_id == user_id:
        return
    if plan.organization_id:
        ContentService(db)._verify_org_access(user_id, plan.organization_id)
        return
    raise ValueError("User does not have access to this generation plan")


def create_plan(db: Session, user_id: int, data) -> ContentGenerationPlan:
    if data.organization_id:
        ContentService(db)._verify_org_access(user_id, data.organization_id)
    next_run = data.next_run_at
    if not next_run.tzinfo:
        next_run = next_run.replace(tzinfo=timezone.utc)
    if next_run <= datetime.now(timezone.utc):
        raise ValueError("The first plan run must be in the future")

    plan = ContentGenerationPlan(
        organization_id=data.organization_id,
        created_by_id=user_id,
        name=data.name,
        category_id=data.category_id,
        category_name=data.category_name,
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
    while next_run <= run_at:
        next_run += interval
    plan.next_run_at = next_run


def run_plan(db: Session, plan: ContentGenerationPlan) -> ContentGenerationPlan:
    """Run one due plan occurrence and advance its cursor after a durable result."""
    if plan.status != GenerationPlanStatus.ACTIVE or not plan.active:
        return plan
    run_at = plan.next_run_at
    idempotency_key = f"generation-plan:{plan.id}:{run_at.isoformat()}"
    generate_and_persist_draft(
        db,
        plan.created_by_id,
        category_id=plan.category_id,
        category_name=plan.category_name,
        extra_instruction=plan.extra_instruction,
        organization_id=plan.organization_id,
        idempotency_key=idempotency_key,
    )
    _advance_plan(plan, run_at)
    db.commit()
    db.refresh(plan)
    return plan


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
    for plan in due:
        try:
            run_plan(db, plan)
            generated += 1
        except Exception:
            db.rollback()
            failed += 1
    return {"generated": generated, "failed": failed, "due": len(due)}
