"""Workspace business intelligence and source provenance routes."""
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.user import User
from app.models.workspace_intelligence import WorkspaceProfile, WorkspaceSource
from app.models.workspace_evidence import WorkspaceClaim, WorkspaceClaimSource
from app.models.content_opportunity import ContentOpportunity
from app.services.opportunity_service import discover_workspace_opportunities
from app.services.workspace_intelligence_service import (
    WorkspaceSourceRefreshError,
    refresh_website_source,
    refresh_workspace_web_sources,
)
from app.schemas.workspace_intelligence import (
    WorkspaceIntelligenceResponse,
    WorkspaceProfileResponse,
    WorkspaceProfileUpsert,
    WorkspaceSourceCreate,
    WorkspaceSourceReview,
    WorkspaceSourceResponse,
    WorkspaceClaimCreate,
    WorkspaceClaimReview,
    WorkspaceClaimResponse,
    ContentOpportunityResponse,
)

router = APIRouter()


def _member_or_403(db: Session, org_id: int, user_id: int, *, write: bool = False) -> OrganizationMember:
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
    if write and member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return member


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _json_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _profile_payload(profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "organization_id": profile.organization_id,
        "business_description": profile.business_description,
        "mission": profile.mission,
        "tagline": profile.tagline,
        "industry": profile.industry,
        "services": _json_list(profile.services_json),
        "products": _json_list(profile.products_json),
        "target_audience": profile.target_audience,
        "locations": _json_list(profile.locations_json),
        "brand_voice": profile.brand_voice,
        "tone": profile.tone,
        "visual_style": profile.visual_style,
        "brand_colors": _json_list(profile.brand_colors_json),
        "font_preferences": _json_list(profile.font_preferences_json),
        "preferred_content_formats": _json_list(profile.preferred_content_formats_json),
        "content_cadence": _json_dict(profile.content_cadence_json),
        "keywords": _json_list(profile.keywords_json),
        "watch_terms": _json_list(profile.watch_terms_json),
        "competitor_urls": _json_list(profile.competitor_urls_json),
        "preferred_languages": _json_list(profile.preferred_languages_json),
        "contact_email": profile.contact_email,
        "contact_phone": profile.contact_phone,
        "whatsapp_display_phone": profile.whatsapp_display_phone,
        "whatsapp_business_account_id": profile.whatsapp_business_account_id,
        "website_url": profile.website_url,
        "linkedin_url": profile.linkedin_url,
        "facebook_url": profile.facebook_url,
        "instagram_url": profile.instagram_url,
        "whatsapp_url": profile.whatsapp_url,
        "logo_media_id": profile.logo_media_id,
        "telegram_approval_chat_id": profile.telegram_approval_chat_id,
        "telegram_approval_user_id": profile.telegram_approval_user_id,
        "telegram_approval_enabled": profile.telegram_approval_enabled,
        "approval_required": profile.approval_required,
        "approved_claims": _json_list(profile.approved_claims_json),
        "prohibited_claims": _json_list(profile.prohibited_claims_json),
        "last_refreshed_at": profile.last_refreshed_at,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def _opportunity_payload(opportunity: ContentOpportunity) -> dict[str, Any]:
    return {
        "id": opportunity.id,
        "organization_id": opportunity.organization_id,
        "source_type": opportunity.source_type,
        "source_url": opportunity.source_url,
        "publisher": opportunity.publisher,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "summary": opportunity.summary,
        "source_published_at": opportunity.source_published_at,
        "discovered_at": opportunity.discovered_at,
        "freshness_score": opportunity.freshness_score,
        "relevance_score": opportunity.relevance_score,
        "trust_score": opportunity.trust_score,
        "status": opportunity.status,
        "metadata": _json_dict(opportunity.metadata_json),
    }


def _source_payload(source: WorkspaceSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "organization_id": source.organization_id,
        "source_type": source.source_type,
        "provider": source.provider,
        "url": source.url,
        "external_id": source.external_id,
        "title": source.title,
        "content_text": source.content_text,
        "excerpt": source.excerpt,
        "metadata": _json_dict(source.metadata_json),
        "trust_level": source.trust_level,
        "review_status": source.review_status,
        "is_active": source.is_active,
        "last_fetched_at": source.last_fetched_at,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
    }


def _claim_payload(claim: WorkspaceClaim) -> dict[str, Any]:
    return {
        "id": claim.id,
        "organization_id": claim.organization_id,
        "claim_text": claim.claim_text,
        "claim_type": claim.claim_type,
        "review_status": claim.review_status,
        "source_ids": [link.source_id for link in claim.evidence_links],
        "metadata": _json_dict(claim.metadata_json),
        "created_at": claim.created_at,
        "updated_at": claim.updated_at,
    }


def _apply_profile(profile: WorkspaceProfile, payload: WorkspaceProfileUpsert) -> None:
    values = payload.model_dump()
    list_fields = {
        "services": "services_json",
        "products": "products_json",
        "locations": "locations_json",
        "brand_colors": "brand_colors_json",
        "font_preferences": "font_preferences_json",
        "preferred_content_formats": "preferred_content_formats_json",
        "content_cadence": "content_cadence_json",
        "keywords": "keywords_json",
        "watch_terms": "watch_terms_json",
        "competitor_urls": "competitor_urls_json",
        "preferred_languages": "preferred_languages_json",
        "approved_claims": "approved_claims_json",
        "prohibited_claims": "prohibited_claims_json",
    }
    for field, value in values.items():
        column = list_fields.get(field, field)
        if field in list_fields:
            value = json.dumps(value, ensure_ascii=False)
        elif value is not None and field.endswith("_url"):
            value = str(value)
        setattr(profile, column, value)


@router.get("/{org_id}/intelligence", response_model=WorkspaceIntelligenceResponse)
def get_workspace_intelligence(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id)
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == org_id).first()
    sources = (
        db.query(WorkspaceSource)
        .filter(WorkspaceSource.organization_id == org_id, WorkspaceSource.is_active.is_(True))
        .order_by(WorkspaceSource.created_at.desc())
        .all()
    )
    claims = db.query(WorkspaceClaim).filter(WorkspaceClaim.organization_id == org_id).order_by(WorkspaceClaim.created_at.desc()).all()
    approved_sources = sum(source.review_status == "approved" for source in sources)
    approved_claims = sum(claim.review_status == "approved" for claim in claims)
    grounding_status = "ready" if approved_sources and approved_claims else ("sources_ready" if approved_sources else "needs_review")
    return {
        "profile": _profile_payload(profile) if profile else None,
        "sources": [_source_payload(source) for source in sources],
        "claims": [_claim_payload(claim) for claim in claims],
        "source_count": len(sources),
        "approved_source_count": approved_sources,
        "claim_count": len(claims),
        "approved_claim_count": approved_claims,
        "grounding_status": grounding_status,
    }


@router.put("/{org_id}/intelligence/profile", response_model=WorkspaceProfileResponse)
def upsert_workspace_profile(
    org_id: int,
    payload: WorkspaceProfileUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == org_id).first()
    if profile is None:
        profile = WorkspaceProfile(organization_id=org_id)
        db.add(profile)
        db.flush()
    _apply_profile(profile, payload)
    db.commit()
    db.refresh(profile)
    return _profile_payload(profile)


@router.get("/{org_id}/intelligence/opportunities", response_model=list[ContentOpportunityResponse])
def list_workspace_opportunities(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id)
    opportunities = (
        db.query(ContentOpportunity)
        .filter(ContentOpportunity.organization_id == org_id)
        .order_by((ContentOpportunity.relevance_score + ContentOpportunity.freshness_score).desc(), ContentOpportunity.discovered_at.desc())
        .limit(100)
        .all()
    )
    return [_opportunity_payload(opportunity) for opportunity in opportunities]


@router.post("/{org_id}/intelligence/opportunities/discover", response_model=list[ContentOpportunityResponse])
def discover_opportunities(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    try:
        opportunities = discover_workspace_opportunities(db, org_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Opportunity discovery failed: {exc}") from exc
    return [_opportunity_payload(opportunity) for opportunity in opportunities]


@router.get("/{org_id}/intelligence/claims", response_model=list[WorkspaceClaimResponse])
def list_workspace_claims(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id)
    claims = db.query(WorkspaceClaim).filter(WorkspaceClaim.organization_id == org_id).order_by(WorkspaceClaim.created_at.desc()).all()
    return [_claim_payload(claim) for claim in claims]


@router.post("/{org_id}/intelligence/claims", response_model=WorkspaceClaimResponse, status_code=status.HTTP_201_CREATED)
def add_workspace_claim(
    org_id: int,
    payload: WorkspaceClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    sources = []
    if payload.source_ids:
        sources = db.query(WorkspaceSource).filter(
            WorkspaceSource.organization_id == org_id,
            WorkspaceSource.id.in_(payload.source_ids),
            WorkspaceSource.is_active.is_(True),
        ).all()
        if {source.id for source in sources} != set(payload.source_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Claim evidence sources must belong to this active workspace")
    claim = WorkspaceClaim(
        organization_id=org_id,
        claim_text=payload.claim_text.strip(),
        claim_type=payload.claim_type,
        review_status=payload.review_status,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=False),
    )
    db.add(claim)
    db.flush()
    for source in sources:
        db.add(WorkspaceClaimSource(claim_id=claim.id, source_id=source.id))
    db.commit()
    db.refresh(claim)
    return _claim_payload(claim)


@router.post("/{org_id}/intelligence/claims/{claim_id}/review", response_model=WorkspaceClaimResponse)
def review_workspace_claim(
    org_id: int,
    claim_id: int,
    payload: WorkspaceClaimReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    claim = db.query(WorkspaceClaim).filter(WorkspaceClaim.id == claim_id, WorkspaceClaim.organization_id == org_id).first()
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace claim not found")
    claim.review_status = payload.review_status
    if payload.review_note:
        metadata = _json_dict(claim.metadata_json)
        metadata["review_note"] = payload.review_note
        claim.metadata_json = json.dumps(metadata, ensure_ascii=False)
    db.commit()
    db.refresh(claim)
    return _claim_payload(claim)


@router.post("/{org_id}/intelligence/sources", response_model=WorkspaceSourceResponse, status_code=status.HTTP_201_CREATED)
def add_workspace_source(
    org_id: int,
    payload: WorkspaceSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    if payload.source_type == "website" and payload.url is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Website sources require a URL")
    source = WorkspaceSource(
        organization_id=org_id,
        source_type=payload.source_type,
        provider=payload.provider,
        url=str(payload.url) if payload.url else None,
        external_id=payload.external_id,
        title=payload.title,
        content_text=payload.content_text,
        excerpt=payload.excerpt,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=False),
        trust_level=payload.trust_level,
        review_status=payload.review_status,
    )
    db.add(source)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This workspace source already exists") from exc
    db.refresh(source)
    return _source_payload(source)


@router.post("/{org_id}/intelligence/sources/{source_id}/refresh", response_model=WorkspaceSourceResponse)
def refresh_workspace_source(
    org_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    source = (
        db.query(WorkspaceSource)
        .filter(
            WorkspaceSource.id == source_id,
            WorkspaceSource.organization_id == org_id,
            WorkspaceSource.is_active.is_(True),
        )
        .first()
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace source not found")
    try:
        return _source_payload(refresh_website_source(db, source))
    except WorkspaceSourceRefreshError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{org_id}/intelligence/sources/{source_id}/review", response_model=WorkspaceSourceResponse)
def review_workspace_source(
    org_id: int,
    source_id: int,
    payload: WorkspaceSourceReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    source = db.query(WorkspaceSource).filter(
        WorkspaceSource.id == source_id,
        WorkspaceSource.organization_id == org_id,
        WorkspaceSource.is_active.is_(True),
    ).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace source not found")
    source.review_status = payload.review_status
    if payload.review_note:
        metadata = _json_dict(source.metadata_json)
        metadata["review_note"] = payload.review_note
        source.metadata_json = json.dumps(metadata, ensure_ascii=False)
    db.commit()
    db.refresh(source)
    return _source_payload(source)


@router.post("/{org_id}/intelligence/refresh")
def refresh_workspace_sources(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    refreshed, errors = refresh_workspace_web_sources(db, org_id)
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == org_id).first()
    if profile:
        profile.last_refreshed_at = datetime.now(timezone.utc)
        db.commit()
    return {
        "refreshed_source_ids": [source.id for source in refreshed],
        "errors": errors,
        "refreshed_count": len(refreshed),
    }


@router.delete("/{org_id}/intelligence/sources/{source_id}")
def remove_workspace_source(
    org_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    source = (
        db.query(WorkspaceSource)
        .filter(
            WorkspaceSource.id == source_id,
            WorkspaceSource.organization_id == org_id,
        )
        .first()
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace source not found")
    source.is_active = False
    db.commit()
    return {"detail": "Workspace source removed"}
