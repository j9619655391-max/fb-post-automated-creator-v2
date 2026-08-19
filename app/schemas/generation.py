from typing import Optional

from pydantic import BaseModel, Field


class GenerateDraftRequest(BaseModel):
    category_id: Optional[int] = None
    category_name: Optional[str] = Field(default=None, max_length=200)
    extra_instruction: Optional[str] = Field(default=None, max_length=2000)
    organization_id: Optional[int] = None
    idempotency_key: Optional[str] = Field(default=None, min_length=8, max_length=128)


class GenerationJobResponse(BaseModel):
    id: int
    status: str
    content_id: Optional[int] = None
    generated_by_ai: bool = True
    title: Optional[str] = None
    body: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
