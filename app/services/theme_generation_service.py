import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content_category import ContentCategory
from app.models.content_generation import ContentGenerationJob, GenerationStatus
from app.models.content_generation_usage import ContentGenerationUsage
from app.models.workspace_intelligence import WorkspaceProfile, WorkspaceSource
from app.services.content_moderation_service import contains_unsubstantiated_outcome_claim
from app.services.genai_client import (
    GenerationUsage,
    active_provider_and_model,
    calculate_cost,
    close_client,
    cost_rates,
    extract_usage,
    get_client,
)


def generate_themes(
    db: Session,
    category_id: Optional[int] = None,
    category_name: Optional[str] = None,
    count: int = 5,
    extra_instruction: Optional[str] = None,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
) -> List[str]:
    """Generate concise advisory themes through the configured AI provider."""
    try:
        provider, model = active_provider_and_model()
    except ValueError:
        return []
    if provider == "gemini" and not settings.gemini_api_key:
        return []
    if provider == "openrouter" and not settings.openrouter_api_key:
        return []

    category_label = "general"
    if category_id:
        cat = db.query(ContentCategory).filter(ContentCategory.id == category_id).first()
        if cat:
            category_label = cat.name
    elif category_name:
        category_label = category_name.strip() or "general"

    profile = (
        db.query(WorkspaceProfile)
        .filter(WorkspaceProfile.organization_id == organization_id)
        .first()
        if organization_id
        else None
    )
    business = ""
    approved_claims = []
    if profile and profile.approved_claims_json:
        try:
            approved_claims = json.loads(profile.approved_claims_json)
        except json.JSONDecodeError:
            approved_claims = []
    approved_source_exists = bool(
        organization_id
        and db.query(WorkspaceSource)
        .filter(
            WorkspaceSource.organization_id == organization_id,
            WorkspaceSource.is_active.is_(True),
            WorkspaceSource.review_status == "approved",
        )
        .first()
    )
    claim_evidence_available = bool(approved_claims or approved_source_exists)
    if profile:
        business = "\n".join(
            line for line in [
                f"Business description: {profile.business_description}" if profile.business_description else "",
                f"Industry: {profile.industry}" if profile.industry else "",
                f"Services: {profile.services_json}" if profile.services_json else "",
                f"Products/offers: {profile.products_json}" if profile.products_json else "",
                f"Audience: {profile.target_audience}" if profile.target_audience else "",
                f"Website: {profile.website_url}" if profile.website_url else "",
            ]
            if line
        )
    prompt = f"""You are a business-aware social media content strategist for Facebook, Instagram, and LinkedIn.
Generate exactly {count} concise content theme ideas for the category: "{category_label}".
Workspace business context:
{business or "No business profile is configured."}

Rules:
- Make themes directly useful for this business's products, services, customers, offers, or brand story.
- Do not default to generic motivation, life advice, or unrelated viral quotes unless the category is explicitly Fashion Quote, Motivation, or Reflection.
- For a fashion/design business, prefer collection showcases, garment details, fabric/craft, styling, bridal/occasion wear, custom orders, customer proof, booking, and relevant seasonal moments.
- Each theme must be one line: a hook idea, topic, or angle.
- Do not claim or imply ROI, traffic growth, conversion lifts, guaranteed results, customer outcomes, or numeric performance without approved evidence.
- Approved evidence is available only when the workspace has explicitly approved claims or an approved source excerpt.
Return ONLY the list, one theme per line, no numbering or bullets."""
    if extra_instruction:
        prompt += f"\nAdditional context: {extra_instruction}"

    job = None
    if user_id is not None:
        job = ContentGenerationJob(
            requested_by_id=user_id,
            category_id=category_id,
            category_name=category_label,
            extra_instruction=extra_instruction,
            organization_id=organization_id,
            model=model,
            provider=provider,
            status=GenerationStatus.GENERATING,
            idempotency_key=f"themes:{uuid.uuid4()}",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    client = None
    usage = GenerationUsage()
    try:
        client = get_client()
        response = client.models.generate_content(model=model, contents=prompt)
        usage = extract_usage(response)
        themes = []
        for raw_line in (getattr(response, "text", "") or "").strip().split("\n"):
            line = raw_line.strip().lstrip("-•* ").strip()
            if not line:
                continue
            if not claim_evidence_available and contains_unsubstantiated_outcome_claim(line):
                continue
            themes.append(line)
            if len(themes) >= count:
                break
        if job:
            job.status = GenerationStatus.SUCCEEDED
            job.completed_at = datetime.now(timezone.utc)
            job.body = json.dumps(themes)
            db.add(
                ContentGenerationUsage(
                    generation_job_id=job.id,
                    organization_id=job.organization_id,
                    requested_by_id=job.requested_by_id,
                    provider=provider,
                    model=model,
                    prompt_token_count=usage.prompt_tokens,
                    candidates_token_count=usage.candidates_tokens,
                    thoughts_token_count=usage.thoughts_tokens,
                    cached_content_token_count=usage.cached_content_tokens,
                    total_token_count=usage.total_tokens,
                    input_cost_per_million_usd=cost_rates(provider)[0],
                    output_cost_per_million_usd=cost_rates(provider)[1],
                    cost_usd=calculate_cost(usage, provider=provider),
                )
            )
            db.commit()
        return themes
    except Exception as exc:
        if job:
            db.rollback()
            job = db.query(ContentGenerationJob).filter(ContentGenerationJob.id == job.id).first()
            if job:
                job.status = GenerationStatus.FAILED
                job.error_code = "THEME_GENERATION_FAILED"
                job.error_message = str(exc)[:1000]
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        return []
    finally:
        if client is not None:
            close_client(client)


def is_theme_generation_available() -> bool:
    try:
        provider, _model = active_provider_and_model()
    except ValueError:
        return False
    return bool(settings.gemini_api_key if provider == "gemini" else settings.openrouter_api_key)
