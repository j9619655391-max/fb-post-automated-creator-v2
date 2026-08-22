"""Deterministic branded-media composition for platform format variants."""

import io
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image, ImageOps
from starlette.datastructures import Headers
from sqlalchemy.orm import Session

from app.models.brand_theme import BrandTheme
from app.models.media import Media
from app.models.workspace_intelligence import WorkspaceProfile
from app.services.media_service import MediaService


FORMAT_SIZES = {
    "facebook": (1200, 630),
    "instagram": (1080, 1080),
    "linkedin": (1200, 627),
}


def _json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
    return parsed


def _color(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = str(value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(char * 2 for char in text)
    if len(text) == 6:
        try:
            return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
        except ValueError:
            pass
    return fallback


def _theme_settings(profile: WorkspaceProfile | None, theme: BrandTheme | None) -> tuple[tuple[int, int, int], str]:
    palette = _json(theme.color_palette_json if theme else None, None)
    if palette is None and profile:
        palette = _json(profile.brand_colors_json, [])
    if isinstance(palette, dict):
        first = next(iter(palette.values()), "#0f172a")
    elif isinstance(palette, list):
        first = palette[0] if palette else "#0f172a"
    else:
        first = "#0f172a"
    return _color(first, (15, 23, 42)), (theme.logo_position if theme else "bottom-right")


def _fit_canvas(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int]) -> Image.Image:
    image = image.convert("RGB")
    fitted = ImageOps.contain(image, size)
    canvas = Image.new("RGB", size, background)
    left = (size[0] - fitted.width) // 2
    top = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (left, top))
    return canvas


def _place_logo(canvas: Image.Image, logo: Image.Image, position: str) -> None:
    logo = logo.convert("RGBA")
    max_width = max(80, int(canvas.width * 0.18))
    max_height = max(40, int(canvas.height * 0.18))
    logo.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    margin = max(20, int(canvas.width * 0.025))
    positions = {
        "top-left": (margin, margin),
        "top-right": (canvas.width - logo.width - margin, margin),
        "bottom-left": (margin, canvas.height - logo.height - margin),
        "bottom-right": (canvas.width - logo.width - margin, canvas.height - logo.height - margin),
    }
    canvas.paste(logo, positions.get(position, positions["bottom-right"]), logo)


def _local_path(media: Media) -> str:
    path = Path(media.stored_path)
    if not path.exists():
        raise ValueError("Source media is not available in the local storage backend")
    return str(path)


def compose_branded_variants(
    db: Session,
    *,
    organization_id: int,
    user_id: int,
    source_media_id: int,
    theme_id: int | None = None,
) -> list[Media]:
    """Create one stored PNG variant per supported platform."""
    source = db.query(Media).filter(Media.id == source_media_id, Media.organization_id == organization_id).first()
    if source is None:
        raise ValueError("Source media does not belong to this workspace")
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    theme = db.query(BrandTheme).filter(BrandTheme.id == theme_id, BrandTheme.organization_id == organization_id).first() if theme_id else None
    logo = None
    if profile and profile.logo_media_id:
        logo_media = db.query(Media).filter(Media.id == profile.logo_media_id, Media.organization_id == organization_id).first()
        if logo_media:
            logo = Image.open(_local_path(logo_media))
    background, logo_position = _theme_settings(profile, theme)
    variants: list[Media] = []
    with Image.open(_local_path(source)) as original:
        for platform, size in FORMAT_SIZES.items():
            canvas = _fit_canvas(original, size, background)
            if logo is not None:
                _place_logo(canvas, logo, logo_position)
            buffer = io.BytesIO()
            canvas.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            filename = f"{platform}-{uuid.uuid4().hex}.png"
            upload = UploadFile(filename=filename, file=buffer, headers=Headers({"content-type": "image/png"}))
            media = MediaService(db).save_upload(upload, user_id, organization_id)
            variants.append(media)
    return variants
