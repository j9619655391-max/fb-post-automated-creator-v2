import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.content_generation import ContentGenerationJob, GenerationStatus
from app.models.content_generation_usage import ContentGenerationUsage
from app.services.genai_client import (
    GenerationUsage,
    active_provider_and_model,
    calculate_cost,
    close_client,
    cost_rates,
    extract_usage,
    get_client,
)


class AIService:
    """Service for optimization and other short-lived AI operations."""

    def __init__(
        self,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ):
        self.db = db
        self.user_id = user_id
        self.organization_id = organization_id
        self.provider, self.model = active_provider_and_model()
        self.client = get_client()

    def _create_usage_job(self) -> Optional[ContentGenerationJob]:
        if self.db is None or self.user_id is None:
            return None
        job = ContentGenerationJob(
            organization_id=self.organization_id,
            requested_by_id=self.user_id,
            category_name="optimization",
            model=self.model,
            provider=self.provider,
            status=GenerationStatus.GENERATING,
            idempotency_key=f"optimization:{uuid.uuid4()}",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def _save_usage(self, job: Optional[ContentGenerationJob], usage: GenerationUsage) -> None:
        if not job or not self.db:
            return
        input_rate, output_rate = cost_rates(job.provider)
        self.db.add(
            ContentGenerationUsage(
                generation_job_id=job.id,
                organization_id=job.organization_id,
                requested_by_id=job.requested_by_id,
                provider=job.provider or self.provider,
                model=job.model or self.model,
                prompt_token_count=usage.prompt_tokens,
                candidates_token_count=usage.candidates_tokens,
                thoughts_token_count=usage.thoughts_tokens,
                cached_content_token_count=usage.cached_content_tokens,
                total_token_count=usage.total_tokens,
                input_cost_per_million_usd=input_rate,
                output_cost_per_million_usd=output_rate,
                cost_usd=calculate_cost(usage, provider=job.provider),
            )
        )

    def optimize_content(self, title: str, body: str) -> Dict[str, str]:
        """Return an optimized title/body and account for provider token usage."""
        prompt = f"""
You are an expert social media manager and copywriter. Review the following draft post:

Title/Subject: {title}
Body: {body}

Please provide an optimized version of this post designed to maximize engagement, clarity, and professionalism on platforms like Facebook and LinkedIn.
Return ONLY a JSON object with two keys containing your optimized strings: "optimized_title" and "optimized_body".
Do not include markdown formatting like ```json or any other text outside the JSON object.
"""
        job = self._create_usage_job()
        usage = GenerationUsage()
        try:
            response = self.client.models.generate_content(
                model=job.model if job else self.model,
                contents=prompt,
            )
            usage = extract_usage(response)
            self._save_usage(job, usage)
            text = (getattr(response, "text", "") or "").strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            result = json.loads(text.strip())
            if job and self.db:
                job.status = GenerationStatus.SUCCEEDED
                job.completed_at = datetime.now(timezone.utc)
                job.title = str(result.get("optimized_title") or title)[:200]
                job.body = str(result.get("optimized_body") or body)
                self.db.commit()
            return {
                "title": result.get("optimized_title", title),
                "body": result.get("optimized_body", body),
            }
        except Exception as exc:
            if job and self.db:
                self.db.rollback()
                job = self.db.query(ContentGenerationJob).filter(ContentGenerationJob.id == job.id).first()
                if job:
                    job.status = GenerationStatus.FAILED
                    job.error_code = "OPTIMIZATION_FAILED"
                    job.error_message = str(exc)[:1000]
                    job.completed_at = datetime.now(timezone.utc)
                    self._save_usage(job, usage)
                    self.db.commit()
            raise ValueError(f"Failed to generate AI response: {exc}") from exc
        finally:
            close_client(self.client)
