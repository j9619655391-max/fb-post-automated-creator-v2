"""Remaining-roadmap APIs: signals, analytics, and automation safety controls."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.content import Content, ContentStatus
from app.models.publishing_metric import PublishingMetric
from app.models.social_signal import SocialSignal
from app.models.user import User
from app.models.workspace_automation import WorkspaceAutomationPolicy
from app.schemas.remaining_roadmap import (
    AnalyticsSummaryResponse,
    AutomationDecisionResponse,
    AutomationPolicyResponse,
    AutomationPolicyUpsert,
    BrandedMediaComposeRequest,
    BrandedMediaVariantResponse,
    CompleteSocialPostComposeRequest,
    CompleteSocialPostPackageResponse,
    PublishingMetricCreate,
    PublishingMetricResponse,
    SocialSignalCreate,
    SocialSignalResponse,
)
from app.services.performance_service import ingest_metric, summarize_performance
from app.services.risk_policy_service import assess_content_risk, autopilot_decision, get_or_create_policy
from app.services.social_listening_service import collect_workspace_signals, create_manual_signal, summarize_signals
from app.services.media_composer_service import compose_branded_variants, compose_generated_text_variants
from app.services.content_package_service import create_content_packages, content_package_payload
from app.services.media_service import MediaService
from app.api.routes.workspace_intelligence import _member_or_403

router = APIRouter()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _policy_payload(policy: WorkspaceAutomationPolicy) -> dict[str, Any]:
    return {
        "id": policy.id,
        "organization_id": policy.organization_id,
        "approval_mode": policy.approval_mode,
        "autopilot_enabled": policy.autopilot_enabled,
        "emergency_stop": policy.emergency_stop,
        "emergency_stop_reason": policy.emergency_stop_reason,
        "max_autopilot_risk_tier": policy.max_autopilot_risk_tier,
        "max_autopilot_posts_per_day": policy.max_autopilot_posts_per_day,
        "max_approval_batch_size": policy.max_approval_batch_size,
        "approval_batch_window_minutes": policy.approval_batch_window_minutes,
        "max_daily_generated_drafts": policy.max_daily_generated_drafts,
        "updated_by_id": policy.updated_by_id,
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
    }


def _signal_payload(signal: SocialSignal) -> dict[str, Any]:
    try:
        metadata = json.loads(signal.metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return {
        "id": signal.id,
        "organization_id": signal.organization_id,
        "signal_type": signal.signal_type,
        "source_type": signal.source_type,
        "source_url": signal.source_url,
        "external_id": signal.external_id,
        "query": signal.query,
        "subject": signal.subject,
        "title": signal.title,
        "excerpt": signal.excerpt,
        "publisher": signal.publisher,
        "published_at": signal.published_at,
        "sentiment": signal.sentiment,
        "sentiment_score": signal.sentiment_score,
        "relevance_score": signal.relevance_score,
        "engagement_count": signal.engagement_count,
        "metadata": metadata,
        "status": signal.status,
        "created_at": signal.created_at,
        "updated_at": signal.updated_at,
    }


@router.get("/{org_id}/signals", response_model=list[SocialSignalResponse])
def list_signals(
    org_id: int,
    signal_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id)
    query = db.query(SocialSignal).filter(SocialSignal.organization_id == org_id, SocialSignal.status != "archived")
    if signal_type:
        query = query.filter(SocialSignal.signal_type == signal_type)
    return [_signal_payload(row) for row in query.order_by(SocialSignal.published_at.desc(), SocialSignal.id.desc()).limit(limit).all()]


@router.get("/{org_id}/signals/summary")
def signal_summary(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id)
    return summarize_signals(db, org_id)


@router.post("/{org_id}/signals/collect", response_model=list[SocialSignalResponse])
def collect_signals(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    return [_signal_payload(row) for row in collect_workspace_signals(db, org_id)]


@router.post("/{org_id}/signals", response_model=SocialSignalResponse, status_code=status.HTTP_201_CREATED)
def add_signal(org_id: int, payload: SocialSignalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    return _signal_payload(create_manual_signal(db, org_id, payload.model_dump()))


@router.get("/{org_id}/analytics", response_model=AnalyticsSummaryResponse)
def analytics_summary(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id)
    return summarize_performance(db, org_id)


@router.get("/{org_id}/analytics/metrics", response_model=list[PublishingMetricResponse])
def list_metrics(org_id: int, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id)
    return db.query(PublishingMetric).filter(PublishingMetric.organization_id == org_id).order_by(PublishingMetric.captured_at.desc()).limit(limit).all()


@router.post("/{org_id}/analytics/metrics", response_model=PublishingMetricResponse, status_code=status.HTTP_201_CREATED)
def add_metric(org_id: int, payload: PublishingMetricCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    try:
        return ingest_metric(db, org_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{org_id}/media/compose", response_model=list[BrandedMediaVariantResponse])
def compose_media(org_id: int, payload: BrandedMediaComposeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    try:
        variants = compose_branded_variants(
            db,
            organization_id=org_id,
            user_id=current_user.id,
            source_media_id=payload.source_media_id,
            theme_id=payload.theme_id,
            template_family=payload.template_family,
            headline=payload.headline,
            body=payload.body,
            cta=payload.cta,
            website=payload.website,
            handle=payload.handle,
            phone=payload.phone,
            whatsapp=payload.whatsapp,
            location=payload.location,
        )
        media_service = MediaService(db)
        return [
            {"id": media.id, "filename": media.filename, "mime_type": media.mime_type, "file_size": media.file_size, "url": media_service.get_public_url(media)}
            for media in variants
        ]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{org_id}/media/compose-package", response_model=list[CompleteSocialPostPackageResponse])
def compose_complete_social_package(
    org_id: int,
    payload: CompleteSocialPostComposeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an approval-required draft with image and per-platform social copy."""
    _member_or_403(db, org_id, current_user.id, write=True)
    headline = payload.headline.strip()
    caption = (payload.caption or payload.body).strip()
    if not headline or not caption:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Headline and caption/body are required")
    use_text_card = payload.use_branded_text_card and payload.template_family == "quote-card"
    if payload.source_media_id is None and not use_text_card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose a workspace-owned source image or explicitly enable the branded quote text-card.",
        )

    try:
        content = Content(
            title=headline,
            body=caption,
            status=ContentStatus.DRAFT,
            organization_id=org_id,
            created_by_id=current_user.id,
            media_id=payload.source_media_id,
        )
        assess_content_risk(content, [])
        db.add(content)
        db.flush()
        if payload.source_media_id is not None:
            variants = compose_branded_variants(
                db,
                organization_id=org_id,
                user_id=current_user.id,
                source_media_id=payload.source_media_id,
                theme_id=payload.theme_id,
                template_family=payload.template_family,
                background_preset=payload.background_preset,
                headline=headline,
                body=payload.body or caption,
                cta=payload.cta,
                website=payload.website,
                handle=payload.handle,
                phone=payload.phone,
                whatsapp=payload.whatsapp,
                location=payload.location,
            )
        else:
            variants = compose_generated_text_variants(
                db,
                organization_id=org_id,
                user_id=current_user.id,
                theme_id=payload.theme_id,
                template_family=payload.template_family,
                background_preset=payload.background_preset,
                headline=headline,
                body=payload.body or caption,
                cta=payload.cta,
                website=payload.website,
                handle=payload.handle,
                phone=payload.phone,
                whatsapp=payload.whatsapp,
                location=payload.location,
            )
        facebook_variant = next((media for media in variants if media.filename.startswith("facebook-")), variants[0] if variants else None)
        if facebook_variant is None:
            raise ValueError("No branded image variants were rendered")
        content.media_id = facebook_variant.id
        variant_by_platform = {media.filename.split("-", 1)[0]: media for media in variants}
        packages = create_content_packages(
            db,
            content.id,
            org_id,
            [str(platform) for platform in payload.platforms],
            payload.theme_id,
            None,
            caption=caption,
            cta=payload.cta,
            hashtags=payload.hashtags,
            tags=payload.tags,
            media_variant_ids_by_platform={platform: [media.id] for platform, media in variant_by_platform.items()},
            image_text=payload.image_text or payload.body or headline,
            alt_text=payload.alt_text or f"{headline}. {payload.image_text or payload.body}",
            objective=payload.objective,
            creative_archetype=payload.creative_archetype or payload.template_family,
            source_refs=payload.source_refs,
            claim_refs=payload.claim_refs,
            visual_brief={
                **payload.visual_brief,
                "template_family": payload.template_family,
                "background_preset": payload.background_preset,
            },
            asset_provenance={
                **payload.asset_provenance,
                "mode": "branded_text_card" if use_text_card else "workspace_media",
                "source_media_id": payload.source_media_id,
            },
            visual_qa_status="not_run",
        )
        media_service = MediaService(db)
        results = []
        for package in packages:
            image = variant_by_platform.get(package.platform)
            if image is None:
                raise ValueError(f"Rendered image missing for {package.platform}")
            package_data = content_package_payload(package)
            results.append(
                {
                    "content_id": content.id,
                    "package_id": package.id,
                    "platform": package.platform,
                    "image": {
                        "id": image.id,
                        "filename": image.filename,
                        "mime_type": image.mime_type,
                        "file_size": image.file_size,
                        "url": media_service.get_public_url(image),
                    },
                    "headline": package_data["headline"] or headline,
                    "image_text": package_data["image_text"],
                    "caption": package_data["caption"],
                    "alt_text": package_data["alt_text"],
                    "cta": package_data["cta"],
                    "objective": package_data["objective"],
                    "creative_archetype": package_data["creative_archetype"],
                    "hashtags": package_data["hashtags"],
                    "tags": package_data["tags"],
                    "source_refs": package_data["source_refs"],
                    "claim_refs": package_data["claim_refs"],
                    "visual_brief": package_data["visual_brief"],
                    "asset_provenance": package_data["asset_provenance"],
                    "visual_qa_status": package_data["visual_qa_status"],
                    "visual_qa_flags": package_data["visual_qa_flags"],
                    "status": package_data["status"],
                }
            )
        return results
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{org_id}/automation/policy", response_model=AutomationPolicyResponse)
def get_policy(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id)
    return _policy_payload(get_or_create_policy(db, org_id))


@router.put("/{org_id}/automation/policy", response_model=AutomationPolicyResponse)
def update_policy(org_id: int, payload: AutomationPolicyUpsert, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    policy = get_or_create_policy(db, org_id)
    for field, value in payload.model_dump().items():
        setattr(policy, field, value)
    policy.updated_by_id = current_user.id
    if policy.approval_mode == "required":
        policy.autopilot_enabled = False
    db.commit()
    db.refresh(policy)
    return _policy_payload(policy)


@router.post("/{org_id}/automation/emergency-stop", response_model=AutomationPolicyResponse)
def trigger_emergency_stop(org_id: int, reason: str = Query(default="Operator emergency stop"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    policy = get_or_create_policy(db, org_id)
    policy.emergency_stop = True
    policy.autopilot_enabled = False
    policy.emergency_stop_reason = reason[:2000]
    policy.updated_by_id = current_user.id
    db.commit()
    db.refresh(policy)
    return _policy_payload(policy)


@router.post("/{org_id}/automation/emergency-stop/clear", response_model=AutomationPolicyResponse)
def clear_emergency_stop(org_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id, write=True)
    policy = get_or_create_policy(db, org_id)
    policy.emergency_stop = False
    policy.emergency_stop_reason = None
    policy.updated_by_id = current_user.id
    db.commit()
    db.refresh(policy)
    return _policy_payload(policy)


@router.get("/{org_id}/automation/content/{content_id}/decision", response_model=AutomationDecisionResponse)
def content_automation_decision(org_id: int, content_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _member_or_403(db, org_id, current_user.id)
    content = db.query(Content).filter(Content.id == content_id, Content.organization_id == org_id).first()
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    assess_content_risk(content)
    db.commit()
    allowed, reason = autopilot_decision(db, org_id, content)
    return {
        "content_id": content.id,
        "risk_score": content.risk_score,
        "risk_tier": content.risk_tier,
        "risk_flags": _json_list(content.risk_flags_json),
        "autopilot_allowed": allowed,
        "reason": reason,
    }
