from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.generation_plan import ApprovalMode, GenerationPlanStatus, GenerationRecurrence


class GenerationPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category_id: Optional[int] = None
    category_name: Optional[str] = Field(default=None, max_length=200)
    extra_instruction: Optional[str] = Field(default=None, max_length=2000)
    organization_id: Optional[int] = None
    recurrence: GenerationRecurrence = GenerationRecurrence.DAILY
    approval_mode: ApprovalMode = ApprovalMode.REQUIRED
    next_run_at: datetime


class GenerationPlanResponse(BaseModel):
    id: int
    name: str
    organization_id: Optional[int]
    created_by_id: int
    category_id: Optional[int]
    category_name: Optional[str]
    recurrence: GenerationRecurrence
    approval_mode: ApprovalMode
    status: GenerationPlanStatus
    next_run_at: datetime
    last_run_at: Optional[datetime]
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
