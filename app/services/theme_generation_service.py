"""AI theme generation using the official Google GenAI SDK. Advisory only."""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content_category import ContentCategory
from app.models.content_generation import ContentGenerationJob, GenerationStatus
from app.models.content_generation_usage import ContentGenerationUsage
from app.services.genai_client import GenerationUsage, calculate_cost, close_client, extract_usage, get_client


def generate_themes(
    db: Session,
    category_id: Optional[int] = None,
    category_name: Optional[str] = None,
    count: int = 5,
    extra_instruction: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[str]:
    """Generate concise advisory themes and account for provider usage when authenticated."""
    if not settings.gemini_api_key:
        return []

    category_label = "general"
    if category_id:
        cat = db.query(ContentCategory).filter(ContentCategory.id == category_id).first()
        if cat:
            category_label = cat.name
    elif category_name:
        category_label = category_name.strip() or "general"

    prompt = f"""You are a creative content strategist for social media (Facebook page posts).
Generate exactly {count} short content theme ideas for the category: "{category_label}".
Each theme should be one line: a hook idea, topic, or angle.
Return ONLY the list, one theme per line, no numbering or bullets.
Keep themes concise, engaging, and suitable for a short post."""
    if extra_instruction:
        prompt += f"\nAdditional context: {extra_instruction}"

    job = None
    if user_id is not None:
        job = ContentGenerationJob(
            requested_by_id=user_id,
            category_id=category_id,
            category_name=category_label,
            extra_instruction=extra_instruction,
            model=settings.gemini_model,
            provider="gemini",
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
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        usage = extract_usage(response)
        themes = [line.strip() for line in (getattr(response, "text", "") or "").strip().split("\n") if line.strip()][:count]
        if job:
            job.status = GenerationStatus.SUCCEEDED
            job.completed_at = datetime.now(timezone.utc)
            job.body = json.dumps(themes)
            db.add(
                ContentGenerationUsage(
                    generation_job_id=job.id,
                    organization_id=job.organization_id,
                    requested_by_id=job.requested_by_id,
                    provider="gemini",
                    model=settings.gemini_model,
                    prompt_token_count=usage.prompt_tokens,
                    candidates_token_count=usage.candidates_tokens,
                    thoughts_token_count=usage.thoughts_tokens,
                    cached_content_token_count=usage.cached_content_tokens,
                    total_token_count=usage.total_tokens,
                    input_cost_per_million_usd=settings.gemini_input_cost_per_million_usd,
                    output_cost_per_million_usd=settings.gemini_output_cost_per_million_usd,
                    cost_usd=calculate_cost(usage),
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
    return bool(settings.gemini_api_key)
