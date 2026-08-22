"""Deterministic branded-media composition for editable social creative templates.

This renderer is intentionally source-controlled and deterministic: exact copy, logo,
contact fields, palette, and placement remain operator-controlled rather than being
invented by an image model. It is suitable for quote cards and fashion creatives
where typography and text placement must be reproducible.
"""

import io
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image, ImageDraw, ImageFont, ImageOps
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
TEMPLATE_FAMILIES = {"fashion-editorial", "product-catalog", "quote-card", "collection-story"}



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



def _theme_settings(profile: WorkspaceProfile | None, theme: BrandTheme | None) -> dict[str, Any]:
    palette = _json(theme.color_palette_json if theme else None, None)
    if palette is None and profile:
        palette = _json(profile.brand_colors_json, [])
    if isinstance(palette, dict):
        colors = list(palette.values())
    elif isinstance(palette, list):
        colors = palette
    else:
        colors = []
    while len(colors) < 4:
        colors.append(["#0f172a", "#f8fafc", "#facc15", "#ec4899"][len(colors)])
    typography = _json(theme.typography_json if theme else None, {})
    if not isinstance(typography, dict):
        typography = {}
    return {
        "primary": _color(colors[0], (15, 23, 42)),
        "surface": _color(colors[1], (248, 250, 252)),
        "accent": _color(colors[2], (250, 204, 21)),
        "highlight": _color(colors[3], (236, 72, 153)),
        "logo_position": theme.logo_position if theme else "bottom-right",
        "background_style": theme.background_style if theme else "image",
        "typography": typography,
    }



def _font(preferences: dict[str, Any], key: str, size: int, italic: bool = False) -> ImageFont.ImageFont:
    configured = preferences.get(key)
    candidates = []
    if isinstance(configured, str) and configured.startswith("/"):
        candidates.append(configured)
    candidates.extend([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf" if italic else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ])
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()



def _fit_canvas(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int]) -> Image.Image:
    image = image.convert("RGB")
    fitted = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    if background:
        return fitted
    return fitted



def _rounded_border(draw: ImageDraw.ImageDraw, size: tuple[int, int], color: tuple[int, int, int], width: int = 4) -> None:
    margin = max(14, min(size) // 45)
    draw.rounded_rectangle((margin, margin, size[0] - margin, size[1] - margin), radius=margin // 2, outline=color, width=width)



def _draw_gradient_overlay(canvas: Image.Image, top_alpha: int = 0, bottom_alpha: int = 170) -> Image.Image:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    height = canvas.height
    for y in range(height):
        ratio = y / max(1, height - 1)
        alpha = int(top_alpha + (bottom_alpha - top_alpha) * ratio)
        draw.line((0, y, canvas.width, y), fill=(0, 0, 0, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")



def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    words = str(text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)



def _text_box(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, spacing: int = 8) -> tuple[str, int, int]:
    wrapped = _wrap(draw, text, font, max_width)
    box = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=spacing)
    return wrapped, box[2] - box[0], box[3] - box[1]



def _place_logo(canvas: Image.Image, logo: Image.Image | None, position: str) -> Image.Image:
    if logo is None:
        return canvas
    target = canvas.convert("RGBA")
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
        "center": ((canvas.width - logo.width) // 2, (canvas.height - logo.height) // 2),
    }
    target.paste(logo, positions.get(position, positions["bottom-right"]), logo)
    return target.convert("RGB")



def _draw_footer(
    draw: ImageDraw.ImageDraw,
    canvas: Image.Image,
    *,
    website: str | None,
    handle: str | None,
    phone: str | None,
    whatsapp: str | None,
    location: str | None,
    color: tuple[int, int, int],
    accent: tuple[int, int, int],
    font: ImageFont.ImageFont,
) -> None:
    parts = [part for part in [website, handle, f"WhatsApp: {whatsapp}" if whatsapp else None, phone, location] if part]
    if not parts:
        return
    footer = "  ·  ".join(parts)
    max_width = canvas.width - 80
    footer, _, _ = _text_box(draw, footer, font, max_width, spacing=2)
    draw.rounded_rectangle((28, canvas.height - 58, canvas.width - 28, canvas.height - 18), radius=12, fill=(0, 0, 0, 125))
    draw.text((canvas.width // 2, canvas.height - 38), footer, font=font, fill=accent, anchor="mm", stroke_width=1, stroke_fill=color)



def _render_template(
    original: Image.Image,
    size: tuple[int, int],
    *,
    family: str,
    headline: str,
    body: str,
    cta: str,
    website: str | None,
    handle: str | None,
    phone: str | None,
    whatsapp: str | None,
    location: str | None,
    logo: Image.Image | None,
    settings: dict[str, Any],
) -> Image.Image:
    primary = settings["primary"]
    surface = settings["surface"]
    accent = settings["accent"]
    highlight = settings["highlight"]
    typography = settings["typography"]
    canvas = _fit_canvas(original, size, primary)
    draw = ImageDraw.Draw(canvas, "RGBA")
    margin = max(40, int(size[0] * 0.07))
    small = _font(typography, "small", max(20, int(size[0] * 0.022)))
    body_font = _font(typography, "body", max(27, int(size[0] * 0.045)))
    heading = _font(typography, "heading", max(36, int(size[0] * 0.068)))
    quote_font = _font(typography, "quote", max(34, int(size[0] * 0.06)), italic=family == "quote-card")

    if family == "quote-card":
        canvas = _draw_gradient_overlay(canvas, 20, 195)
        draw = ImageDraw.Draw(canvas, "RGBA")
        _rounded_border(draw, size, highlight, width=max(3, size[0] // 300))
        draw.text((margin, margin - 6), "“", font=_font(typography, "quote_mark", max(78, int(size[0] * 0.14))), fill=accent)
        quote, _, quote_height = _text_box(draw, body or headline, quote_font, size[0] - margin * 2, spacing=12)
        draw.multiline_text((size[0] // 2, int(size[1] * 0.49)), quote, font=quote_font, fill=surface, anchor="mm", align="center", spacing=12, stroke_width=1, stroke_fill=primary)
        if headline and headline != body:
            draw.text((size[0] // 2, int(size[1] * 0.18)), headline.upper(), font=small, fill=accent, anchor="mm")
        if cta:
            draw.text((size[0] // 2, int(size[1] * 0.83)), cta, font=small, fill=accent, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    if family == "product-catalog":
        canvas = _draw_gradient_overlay(canvas, 0, 150)
        draw = ImageDraw.Draw(canvas, "RGBA")
        panel_top = int(size[1] * 0.50)
        draw.rounded_rectangle((margin // 2, panel_top, size[0] - margin // 2, size[1] - margin // 2), radius=22, fill=(*primary, 220))
        title, _, _ = _text_box(draw, headline or "New design", heading, size[0] - margin * 2, spacing=4)
        draw.multiline_text((margin, panel_top + 30), title, font=heading, fill=surface, spacing=4)
        detail, _, _ = _text_box(draw, body or "Made for your next occasion.", body_font, size[0] - margin * 2, spacing=4)
        draw.multiline_text((margin, panel_top + 30 + int(size[1] * 0.10) + 18), detail, font=body_font, fill=surface, spacing=4)
        if cta:
            draw.rounded_rectangle((margin, size[1] - margin - 82, size[0] - margin, size[1] - margin - 24), radius=18, fill=accent)
            draw.text((size[0] // 2, size[1] - margin - 53), cta, font=small, fill=primary, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    if family == "collection-story":
        canvas = _draw_gradient_overlay(canvas, 0, 100)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle((0, 0, size[0], int(size[1] * 0.18)), fill=surface)
        draw.text((size[0] // 2, int(size[1] * 0.09)), (headline or "Collection story").upper(), font=small, fill=primary, anchor="mm")
        draw.rounded_rectangle((margin, int(size[1] * 0.25), size[0] - margin, int(size[1] * 0.72)), radius=24, outline=accent, width=max(3, size[0] // 300))
        quote, _, _ = _text_box(draw, body or "Designed around your story.", quote_font, size[0] - margin * 3, spacing=8)
        draw.multiline_text((size[0] // 2, int(size[1] * 0.51)), quote, font=quote_font, fill=surface, anchor="mm", align="center", spacing=8)
        if cta:
            draw.text((size[0] // 2, int(size[1] * 0.78)), cta, font=small, fill=accent, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    # fashion-editorial: image-led, left-safe editorial panel.
    canvas = _draw_gradient_overlay(canvas, 0, 125)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((margin // 2, margin // 2, int(size[0] * 0.57), size[1] - margin // 2), radius=26, fill=(*primary, 185))
    title, _, _ = _text_box(draw, headline or "Designed for your moment", heading, int(size[0] * 0.49), spacing=6)
    draw.multiline_text((margin, int(size[1] * 0.22)), title, font=heading, fill=surface, spacing=6)
    detail, _, _ = _text_box(draw, body or "Crafted details. Personal style.", body_font, int(size[0] * 0.45), spacing=5)
    draw.multiline_text((margin, int(size[1] * 0.55)), detail, font=body_font, fill=surface, spacing=5)
    if cta:
        draw.text((margin, int(size[1] * 0.80)), cta, font=small, fill=accent)
    _place_logo(canvas.convert("RGBA"), logo, settings["logo_position"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_footer(draw, canvas, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
    return canvas



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
    template_family: str = "fashion-editorial",
    headline: str = "",
    body: str = "",
    cta: str = "",
    website: str | None = None,
    handle: str | None = None,
    phone: str | None = None,
    whatsapp: str | None = None,
    location: str | None = None,
) -> list[Media]:
    """Create one exact-size stored PNG variant per platform using a named template."""
    if template_family not in TEMPLATE_FAMILIES:
        raise ValueError(f"Unsupported template family: {template_family}")
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
    settings = _theme_settings(profile, theme)
    website = website or (profile.website_url if profile else None)
    phone = phone or (profile.contact_phone if profile else None)
    whatsapp = whatsapp or (profile.whatsapp_display_phone if profile else None)
    location = location or (profile.locations_json if profile else None)
    handle = handle or None
    variants: list[Media] = []
    with Image.open(_local_path(source)) as original:
        for platform, size in FORMAT_SIZES.items():
            rendered = _render_template(
                original,
                size,
                family=template_family,
                headline=headline,
                body=body,
                cta=cta,
                website=website,
                handle=handle,
                phone=phone,
                whatsapp=whatsapp,
                location=location,
                logo=logo,
                settings=settings,
            )
            buffer = io.BytesIO()
            rendered.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            filename = f"{platform}-{template_family}-{uuid.uuid4().hex}.png"
            upload = UploadFile(filename=filename, file=buffer, headers=Headers({"content-type": "image/png"}))
            variants.append(MediaService(db).save_upload(upload, user_id, organization_id))
    return variants
