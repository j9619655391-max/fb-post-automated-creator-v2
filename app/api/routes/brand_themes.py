import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.brand_theme import BrandTheme
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.user import User
from app.schemas.brand_theme import BrandThemeResponse, BrandThemeUpsert

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


def _payload(theme: BrandTheme) -> dict[str, Any]:
    return {
        "id": theme.id,
        "organization_id": theme.organization_id,
        "name": theme.name,
        "slug": theme.slug,
        "description": theme.description,
        "visual_style": theme.visual_style,
        "color_palette": _json_list(theme.color_palette_json),
        "typography": _json_dict(theme.typography_json),
        "logo_position": theme.logo_position,
        "background_style": theme.background_style,
        "supported_formats": _json_list(theme.supported_formats_json),
        "is_active": theme.is_active,
        "is_default": theme.is_default,
        "created_at": theme.created_at,
        "updated_at": theme.updated_at,
    }


def _apply(theme: BrandTheme, payload: BrandThemeUpsert) -> None:
    values = payload.model_dump()
    theme.name = values["name"]
    theme.slug = values["slug"]
    theme.description = values["description"]
    theme.visual_style = values["visual_style"]
    theme.color_palette_json = json.dumps(values["color_palette"], ensure_ascii=False)
    theme.typography_json = json.dumps(values["typography"], ensure_ascii=False)
    theme.logo_position = values["logo_position"]
    theme.background_style = values["background_style"]
    theme.supported_formats_json = json.dumps(values["supported_formats"], ensure_ascii=False)
    theme.is_active = values["is_active"]
    theme.is_default = values["is_default"]


def _clear_other_defaults(db: Session, org_id: int, selected_id: int | None = None) -> None:
    query = db.query(BrandTheme).filter(
        BrandTheme.organization_id == org_id,
        BrandTheme.is_default.is_(True),
    )
    if selected_id is not None:
        query = query.filter(BrandTheme.id != selected_id)
    query.update({BrandTheme.is_default: False}, synchronize_session=False)


@router.get("/{org_id}/themes", response_model=list[BrandThemeResponse])
def list_themes(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id)
    themes = (
        db.query(BrandTheme)
        .filter(BrandTheme.organization_id == org_id)
        .order_by(BrandTheme.is_default.desc(), BrandTheme.name.asc())
        .all()
    )
    return [_payload(theme) for theme in themes]


@router.post("/{org_id}/themes", response_model=BrandThemeResponse, status_code=status.HTTP_201_CREATED)
def create_theme(
    org_id: int,
    payload: BrandThemeUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    if payload.is_default:
        _clear_other_defaults(db, org_id)
    theme = BrandTheme(organization_id=org_id)
    _apply(theme, payload)
    db.add(theme)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Theme slug already exists in this workspace") from exc
    db.refresh(theme)
    return _payload(theme)


@router.put("/{org_id}/themes/{theme_id}", response_model=BrandThemeResponse)
def update_theme(
    org_id: int,
    theme_id: int,
    payload: BrandThemeUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    theme = db.query(BrandTheme).filter(BrandTheme.id == theme_id, BrandTheme.organization_id == org_id).first()
    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    if payload.is_default:
        _clear_other_defaults(db, org_id, selected_id=theme.id)
    _apply(theme, payload)
    db.commit()
    db.refresh(theme)
    return _payload(theme)


@router.delete("/{org_id}/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_theme(
    org_id: int,
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _member_or_403(db, org_id, current_user.id, write=True)
    theme = db.query(BrandTheme).filter(BrandTheme.id == theme_id, BrandTheme.organization_id == org_id).first()
    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    db.delete(theme)
    db.commit()
