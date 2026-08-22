"""Explainable content risk scoring and workspace automation guards."""

import json
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.models.workspace_automation import WorkspaceAutomationPolicy
from app.services.content_moderation_service import moderate_generated_post


RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def assess_text_risk(title: str, body: str, risk_flags: Iterable[str] | None = None) -> tuple[int, str, list[str]]:
    """Return an explainable score, tier, and flags for content under review."""
    moderation = moderate_generated_post(title, body, risk_flags=risk_flags or [])
    flags = list(dict.fromkeys(moderation.flags))
    score = 0
    if any(not flag.startswith("ai_review:") for flag in flags):
        score = 100
    elif flags:
        score = min(79, 35 + 10 * len(flags))
    lowered = f"{title or ''} {body or ''}".casefold()
    if any(term in lowered for term in ("guaranteed", "risk-free", "urgent payment", "act now")):
        score = min(100, score + 15)
        flags.append("persuasive_claim_review")
    if len(body or "") > 2500:
        score = min(100, score + 5)
        flags.append("long_copy_review")
    if score >= 80:
        tier = "critical"
    elif score >= 50:
        tier = "high"
    elif score >= 20:
        tier = "medium"
    else:
        tier = "low"
    return score, tier, list(dict.fromkeys(flags))


def assess_content_risk(content: Content, risk_flags: Iterable[str] | None = None) -> Content:
    score, tier, flags = assess_text_risk(content.title, content.body, risk_flags)
    content.risk_score = score
    content.risk_tier = tier
    content.risk_flags_json = json.dumps(flags, ensure_ascii=False)
    return content


def get_or_create_policy(db: Session, organization_id: int) -> WorkspaceAutomationPolicy:
    policy = db.query(WorkspaceAutomationPolicy).filter(WorkspaceAutomationPolicy.organization_id == organization_id).first()
    if policy is None:
        policy = WorkspaceAutomationPolicy(organization_id=organization_id)
        db.add(policy)
        db.flush()
    return policy


def _published_today(db: Session, organization_id: int) -> int:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(ContentPublishStatus)
        .join(Content, Content.id == ContentPublishStatus.content_id)
        .filter(
            Content.organization_id == organization_id,
            ContentPublishStatus.status == PublishStatusEnum.POSTED,
            ContentPublishStatus.created_at >= start,
        )
        .count()
    )


def autopilot_decision(db: Session, organization_id: int, content: Content) -> tuple[bool, str]:
    """Return whether a draft may bypass a new manual approval, never publish it."""
    policy = get_or_create_policy(db, organization_id)
    if policy.emergency_stop:
        return False, "workspace_emergency_stop"
    if policy.approval_mode != "controlled" or not policy.autopilot_enabled:
        return False, "approval_required"
    if policy.max_autopilot_posts_per_day <= 0:
        return False, "autopilot_daily_cap_disabled"
    if RISK_RANK.get(content.risk_tier or "low", 3) > RISK_RANK.get(policy.max_autopilot_risk_tier or "low", 0):
        return False, "risk_tier_exceeds_policy"
    if _published_today(db, organization_id) >= policy.max_autopilot_posts_per_day:
        return False, "autopilot_daily_cap_reached"
    return True, "controlled_autopilot_allowed"
