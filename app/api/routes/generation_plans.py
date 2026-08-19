from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.generation_plan import GenerationPlanStatus
from app.models.user import User
from app.schemas.generation_plan import GenerationPlanCreate, GenerationPlanResponse
from app.services.generation_plan_service import (
    create_plan,
    get_plan,
    list_plans,
    run_plan,
    set_plan_status,
)

router = APIRouter()


@router.post("/", response_model=GenerationPlanResponse, status_code=status.HTTP_201_CREATED)
def create_generation_plan(
    data: GenerationPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_plan(db, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=List[GenerationPlanResponse])
def list_generation_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_plans(db, current_user.id)


@router.get("/{plan_id}", response_model=GenerationPlanResponse)
def get_generation_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = get_plan(db, plan_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not plan:
        raise HTTPException(status_code=404, detail="Generation plan not found")
    return plan


@router.post("/{plan_id}/pause", response_model=GenerationPlanResponse)
def pause_generation_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return set_plan_status(db, plan_id, current_user.id, GenerationPlanStatus.PAUSED)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{plan_id}/resume", response_model=GenerationPlanResponse)
def resume_generation_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return set_plan_status(db, plan_id, current_user.id, GenerationPlanStatus.ACTIVE)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{plan_id}/run-now", response_model=GenerationPlanResponse)
def run_generation_plan_now(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = get_plan(db, plan_id, current_user.id)
        if not plan:
            raise ValueError("Generation plan not found")
        if plan.status != GenerationPlanStatus.ACTIVE:
            raise ValueError("Generation plan is paused")
        # Run-now is intentionally still approval-required. It only creates a draft.
        return run_plan(db, plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
