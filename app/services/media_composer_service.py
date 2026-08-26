"""Deterministic branded-media composition for editable social creative templates.

This renderer is intentionally source-controlled and deterministic: exact copy, logo,
contact fields, palette, and placement remain operator-controlled rather than being
invented by an image model. It is suitable for quote cards and fashion creatives
where typography and text placement must be reproducible.
"""

import io
import json
import os
import re
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
from app.models.organization import Organization
from app.services.media_service import MediaService


FORMAT_SIZES = {
    "facebook": (1200, 630),
    "instagram": (1080, 1080),
    "linkedin": (1200, 627),
}
TEMPLATE_FAMILIES = {
    "fashion-editorial",
    "service-editorial",
    "product-catalog",
    "quote-card",
    "collection-story",
    "technology-explainer",
}
CREATIVE_ARCHETYPE_CATALOG = {
    "service-announcement": {"objective": "awareness", "template_family": "service-editorial", "asset_requirement": "workspace_media_or_branded_fallback"},
    "technology-explainer": {"objective": "education", "template_family": "technology-explainer", "asset_requirement": "workspace_media_or_branded_fallback"},
    "educational-explainer": {"objective": "education", "template_family": "collection-story", "asset_requirement": "workspace_media_or_branded_fallback"},
    "product-showcase": {"objective": "product discovery", "template_family": "product-catalog", "asset_requirement": "workspace_media_required"},
    "offer-card": {"objective": "conversion", "template_family": "product-catalog", "asset_requirement": "workspace_media_required"},
    "case-study-proof": {"objective": "proof", "template_family": "collection-story", "asset_requirement": "approved_evidence_required"},
    "customer-story": {"objective": "proof", "template_family": "fashion-editorial", "asset_requirement": "approved_evidence_required"},
    "behind-the-scenes": {"objective": "community", "template_family": "fashion-editorial", "asset_requirement": "workspace_media_required"},
    "seasonal-campaign": {"objective": "awareness", "template_family": "collection-story", "asset_requirement": "workspace_media_or_branded_fallback"},
    "quote-card": {"objective": "community", "template_family": "quote-card", "asset_requirement": "branded_fallback_allowed"},
    "collection-story": {"objective": "product discovery", "template_family": "collection-story", "asset_requirement": "workspace_media_or_branded_fallback"},
}
TEMPLATE_COPY_BUDGETS = {
    # These are image-overlay budgets, not caption budgets. Captions may remain
    # long, but the image must stay concise enough for a real social safe area.
    "fashion-editorial": (48, 60),
    "service-editorial": (48, 60),
    "product-catalog": (48, 60),
    "technology-explainer": (52, 68),
    "quote-card": (140, 140),
    "collection-story": (52, 68),
}
QUOTE_BACKGROUND_PRESETS = {
    "midnight-aurora": "Deep midnight field with soft aurora glow",
    "warm-paper": "Warm paper field with terracotta editorial accents",
    "rose-editorial": "Plum field with asymmetric rose editorial panel",
    "sunset-glow": "Coral, saffron, and plum diagonal glow",
    "minimal-ink": "Off-white minimal ink layout with one accent rule",
    "neon-night": "Charcoal field with electric cyan and pink geometry",
}


def _blend_color(first: tuple[int, int, int], second: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(int(a + (b - a) * ratio) for a, b in zip(first, second))  # type: ignore[return-value]


def _linear_gradient(size: tuple[int, int], start: tuple[int, int, int], end: tuple[int, int, int], diagonal: bool = False) -> Image.Image:
    image = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(image)
    width, height = size
    if diagonal:
        for x in range(width):
            ratio = x / max(1, width - 1)
            draw.line((x, 0, x, height), fill=_blend_color(start, end, ratio))
    else:
        for y in range(height):
            ratio = y / max(1, height - 1)
            draw.line((0, y, width, y), fill=_blend_color(start, end, ratio))
    return image


def _apply_quote_background(
    canvas: Image.Image,
    preset: str,
    primary: tuple[int, int, int],
    surface: tuple[int, int, int],
    accent: tuple[int, int, int],
    highlight: tuple[int, int, int],
) -> Image.Image:
    """Paint a distinct, text-safe quote background without generating copy."""
    preset = preset if preset in QUOTE_BACKGROUND_PRESETS else "midnight-aurora"
    width, height = canvas.size
    if preset == "warm-paper":
        base = Image.new("RGB", (width, height), surface)
        draw = ImageDraw.Draw(base, "RGBA")
        for y in range(0, height, max(18, height // 28)):
            draw.line((0, y, width, y), fill=(*primary, 12), width=1)
        draw.ellipse((-int(width * 0.18), int(height * 0.58), int(width * 0.35), int(height * 1.15)), fill=(*accent, 34))
        draw.rounded_rectangle((int(width * 0.055), int(height * 0.055), int(width * 0.945), int(height * 0.945)), radius=28, outline=(*accent, 210), width=max(3, width // 300))
        return base
    if preset == "rose-editorial":
        base = _linear_gradient((width, height), primary, _blend_color(primary, highlight, 0.52))
        draw = ImageDraw.Draw(base, "RGBA")
        draw.rounded_rectangle((int(width * 0.06), int(height * 0.13), int(width * 0.94), int(height * 0.86)), radius=36, fill=(*highlight, 28), outline=(*surface, 170), width=max(2, width // 420))
        draw.rectangle((0, 0, int(width * 0.16), height), fill=(*highlight, 112))
        draw.line((int(width * 0.20), int(height * 0.08), int(width * 0.92), int(height * 0.08)), fill=(*surface, 150), width=max(2, width // 420))
        return base
    if preset == "sunset-glow":
        base = _linear_gradient((width, height), _blend_color(highlight, accent, 0.25), primary, diagonal=True)
        draw = ImageDraw.Draw(base, "RGBA")
        draw.ellipse((int(width * 0.58), -int(height * 0.30), int(width * 1.15), int(height * 0.42)), fill=(*surface, 30))
        draw.ellipse((-int(width * 0.24), int(height * 0.70), int(width * 0.30), int(height * 1.25)), fill=(*accent, 60))
        draw.rounded_rectangle((int(width * 0.07), int(height * 0.14), int(width * 0.93), int(height * 0.80)), radius=34, fill=(*surface, 218))
        return base
    if preset == "minimal-ink":
        base = Image.new("RGB", (width, height), surface)
        draw = ImageDraw.Draw(base, "RGBA")
        draw.line((int(width * 0.08), int(height * 0.14), int(width * 0.92), int(height * 0.14)), fill=(*accent, 255), width=max(4, width // 180))
        draw.line((int(width * 0.08), int(height * 0.86), int(width * 0.92), int(height * 0.86)), fill=(*primary, 180), width=max(2, width // 360))
        draw.ellipse((int(width * 0.80), -int(height * 0.16), int(width * 1.12), int(height * 0.18)), fill=(*highlight, 35))
        return base
    if preset == "neon-night":
        base = Image.new("RGB", (width, height), _blend_color(primary, (3, 7, 18), 0.62))
        draw = ImageDraw.Draw(base, "RGBA")
        draw.line((0, int(height * 0.86), int(width * 0.28), 0), fill=(*accent, 230), width=max(5, width // 180))
        draw.line((int(width * 0.72), height, width, int(height * 0.16)), fill=(*highlight, 230), width=max(5, width // 180))
        draw.polygon([(int(width * 0.72), 0), (width, 0), (width, int(height * 0.22))], fill=(*accent, 35))
        draw.polygon([(0, int(height * 0.74)), (0, height), (int(width * 0.28), height)], fill=(*highlight, 28))
        return base
    # midnight-aurora: keep the strongest contrast for truth and pain quotes.
    base = _linear_gradient((width, height), _blend_color(primary, (3, 7, 18), 0.35), (3, 7, 18))
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow, "RGBA")
    draw.ellipse((int(width * 0.60), -int(height * 0.22), int(width * 1.18), int(height * 0.48)), fill=(*highlight, 38))
    draw.ellipse((-int(width * 0.18), int(height * 0.62), int(width * 0.46), int(height * 1.18)), fill=(*accent, 24))
    return Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")



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
        # Break unusually long tokens (URLs, handles, model names) instead of
        # allowing a single unbreakable token to escape the safe text width.
        chunks: list[str] = []
        remainder = word
        while remainder and draw.textlength(remainder, font=font) > max_width:
            chunk = ""
            for char in remainder:
                candidate_chunk = chunk + char
                if chunk and draw.textlength(candidate_chunk + "…", font=font) > max_width:
                    break
                chunk = candidate_chunk
            if not chunk:
                break
            chunks.append(chunk)
            remainder = remainder[len(chunk):]
        if remainder:
            chunks.append(remainder)
        for piece in chunks:
            candidate = f"{current} {piece}".strip()
            if not current or draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = piece
    if current:
        lines.append(current)
    return "\n".join(lines)



def _text_box(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, spacing: int = 8) -> tuple[str, int, int]:
    wrapped = _wrap(draw, text, font, max_width)
    box = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=spacing)
    return wrapped, box[2] - box[0], box[3] - box[1]


def _fit_quote_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    preferences: dict[str, Any],
    max_width: int,
    max_height: int,
    start_size: int,
) -> tuple[ImageFont.ImageFont, str, int]:
    """Choose the largest quote font that fits the safe text area."""
    size = start_size
    while size >= 34:
        font = _font(preferences, "quote", size, italic=True)
        wrapped, _, height = _text_box(draw, text, font, max_width, spacing=max(8, size // 6))
        if height <= max_height:
            return font, wrapped, max(8, size // 6)
        size -= 4
    font = _font(preferences, "quote", 34, italic=True)
    wrapped, _, height = _text_box(draw, text, font, max_width, spacing=8)
    return font, wrapped, 8



def _fit_template_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    preferences: dict[str, Any],
    *,
    font_key: str,
    max_width: int,
    max_height: int,
    start_size: int,
    min_size: int = 18,
    italic: bool = False,
    spacing: int = 5,
) -> tuple[ImageFont.ImageFont, str, int]:
    """Fit overlay copy into a measured box and ellipsize as a final guard.

    Font shrinking alone is insufficient: a long string can still exceed the
    box at the minimum size. The final candidate is therefore shortened by
    words until both width and height fit, keeping the caption outside the
    image as the complete version.
    """
    size = start_size
    while size >= min_size:
        font = _font(preferences, font_key, size, italic=italic)
        wrapped, _, height = _text_box(draw, text, font, max_width, spacing=spacing)
        if height <= max_height:
            return font, wrapped, spacing
        size -= 2
    font = _font(preferences, font_key, min_size, italic=italic)
    final_spacing = max(2, spacing - 1)
    candidate = " ".join(str(text or "").split())
    words = candidate.split()
    while words:
        shortened = " ".join(words)
        if len(words) < len(candidate.split()):
            shortened += "…"
        wrapped, _, height = _text_box(draw, shortened, font, max_width, spacing=final_spacing)
        if height <= max_height:
            return font, wrapped, final_spacing
        words.pop()
    return font, "…", final_spacing



def _compact_overlay_text(value: str | None, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def prepare_image_overlay_cta(value: str | None, max_chars: int = 36) -> str:
    """Return a short CTA that fits the reserved button or footer-safe zone."""
    return _compact_overlay_text(value, max_chars)


def prepare_image_overlay_copy(family: str, headline: str | None, body: str | None) -> tuple[str, str]:
    """Return the concise headline/body that is allowed inside an image.

    The complete caption remains outside the image. This helper is shared by
    AI and Creative Studio callers so package metadata describes the text that
    was actually rendered, not an unsafe long caption.
    """
    headline_limit, body_limit = TEMPLATE_COPY_BUDGETS.get(family, (48, 60))
    if family == "quote-card":
        return _compact_overlay_text(headline, 80), _compact_overlay_text(body or headline, 140)
    return _compact_overlay_text(headline, headline_limit), _compact_overlay_text(body, body_limit)


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
    brand_label: str | None = None,
    website: str | None,
    handle: str | None,
    phone: str | None,
    whatsapp: str | None,
    location: str | None,
    color: tuple[int, int, int],
    accent: tuple[int, int, int],
    font: ImageFont.ImageFont,
) -> None:
    parts = [part for part in [brand_label, website, handle, f"WhatsApp: {whatsapp}" if whatsapp else None, phone, location] if str(part or "").strip() and str(part).strip() not in {"[]", "{}", "null"}]
    if not parts:
        return
    footer = _compact_overlay_text("  ·  ".join(parts), 96)
    max_width = canvas.width - 80
    footer_font, footer, _ = _fit_template_text(
        draw,
        footer,
        {"small": font},
        font_key="small",
        max_width=max_width,
        max_height=30,
        start_size=max(14, getattr(font, "size", 20) or 20),
        min_size=12,
        spacing=2,
    )
    draw.rounded_rectangle((28, canvas.height - 58, canvas.width - 28, canvas.height - 18), radius=12, fill=(0, 0, 0, 125))
    draw.text((canvas.width // 2, canvas.height - 38), footer, font=footer_font, fill=accent, anchor="mm", stroke_width=1, stroke_fill=color)



def _render_template(
    original: Image.Image,
    size: tuple[int, int],
    *,
    family: str,
    background_preset: str = "midnight-aurora",
    headline: str,
    body: str,
    cta: str,
    website: str | None,
    handle: str | None,
    phone: str | None,
    whatsapp: str | None,
    location: str | None,
    brand_label: str | None = None,
    logo: Image.Image | None = None,
    settings: dict[str, Any] | None = None,
) -> Image.Image:
    settings = settings or _theme_settings(None, None)
    cta = prepare_image_overlay_cta(cta)
    headline, body = prepare_image_overlay_copy(family, headline, body)
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
        canvas = _apply_quote_background(canvas, background_preset, primary, surface, accent, highlight)
        draw = ImageDraw.Draw(canvas, "RGBA")
        _rounded_border(draw, size, highlight, width=max(3, size[0] // 300))
        draw.text((margin, margin - 6), "“", font=_font(typography, "quote_mark", max(78, int(size[0] * 0.14))), fill=accent)
        quote_font, quote, quote_spacing = _fit_quote_font(
            draw,
            body or headline,
            typography,
            size[0] - margin * 2,
            int(size[1] * 0.45),
            max(44, int(size[0] * 0.072)),
        )
        draw.multiline_text((size[0] // 2, int(size[1] * 0.48)), quote, font=quote_font, fill=surface, anchor="mm", align="center", spacing=quote_spacing, stroke_width=1, stroke_fill=primary)
        if headline and headline != body:
            draw.text((size[0] // 2, int(size[1] * 0.18)), headline.upper(), font=small, fill=accent, anchor="mm")
        if cta:
            draw.text((size[0] // 2, int(size[1] * 0.83)), cta, font=small, fill=accent, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, brand_label=brand_label, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    if family == "product-catalog":
        canvas = _draw_gradient_overlay(canvas, 0, 150)
        draw = ImageDraw.Draw(canvas, "RGBA")
        panel_top = int(size[1] * 0.46)
        draw.rounded_rectangle((margin // 2, panel_top, size[0] - margin // 2, size[1] - margin // 2), radius=22, fill=(*primary, 220))
        title_height = int(size[1] * 0.10)
        title_font, title, title_spacing = _fit_template_text(
            draw,
            headline or "New design",
            typography,
            font_key="heading",
            max_width=size[0] - margin * 2,
            max_height=title_height,
            start_size=max(30, int(size[0] * 0.068)),
            min_size=22,
            spacing=4,
        )
        title_y = panel_top + 28
        draw.multiline_text((margin, title_y), title, font=title_font, fill=surface, spacing=title_spacing)
        detail_top = panel_top + title_height + 18
        detail_height = int(size[1] * 0.12)
        detail_font, detail, detail_spacing = _fit_template_text(
            draw,
            body or "Made for your next occasion.",
            typography,
            font_key="body",
            max_width=size[0] - margin * 2,
            max_height=detail_height,
            start_size=max(24, int(size[0] * 0.045)),
            min_size=18,
            spacing=4,
        )
        draw.multiline_text((margin, detail_top), detail, font=detail_font, fill=surface, spacing=detail_spacing)
        if cta:
            # Keep the CTA in its own zone above the footer strip. The previous
            # bottom-anchored position could paint the button over branding.
            footer_height = 58
            footer_gap = max(12, int(size[1] * 0.02))
            cta_height = 58
            cta_y = size[1] - footer_height - footer_gap - (cta_height // 2)
            draw.rounded_rectangle((margin, cta_y - cta_height // 2, size[0] - margin, cta_y + cta_height // 2), radius=18, fill=accent)
            cta_font, cta_text, cta_spacing = _fit_template_text(
                draw,
                cta,
                typography,
                font_key="small",
                max_width=size[0] - margin * 2,
                max_height=34,
                start_size=max(18, int(size[0] * 0.022)),
                min_size=14,
                spacing=2,
            )
            draw.text((size[0] // 2, cta_y), cta_text, font=cta_font, fill=primary, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, brand_label=brand_label, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    if family in {"collection-story", "technology-explainer"}:
        canvas = _draw_gradient_overlay(canvas, 0, 100)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle((0, 0, size[0], int(size[1] * 0.18)), fill=surface)
        draw.text((size[0] // 2, int(size[1] * 0.09)), (headline or "Collection story").upper(), font=small, fill=primary, anchor="mm")
        draw.rounded_rectangle((margin, int(size[1] * 0.25), size[0] - margin, int(size[1] * 0.72)), radius=24, outline=accent, width=max(3, size[0] // 300))
        story_font, quote, story_spacing = _fit_template_text(
            draw,
            body or "Designed around your story.",
            typography,
            font_key="quote",
            max_width=size[0] - margin * 3,
            max_height=int(size[1] * 0.34),
            start_size=max(34, int(size[0] * 0.06)),
            min_size=24,
            italic=True,
            spacing=8,
        )
        draw.multiline_text((size[0] // 2, int(size[1] * 0.51)), quote, font=story_font, fill=surface, anchor="mm", align="center", spacing=story_spacing)
        if cta:
            draw.text((size[0] // 2, int(size[1] * 0.78)), cta, font=small, fill=accent, anchor="mm")
        canvas = _place_logo(canvas, logo, settings["logo_position"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        _draw_footer(draw, canvas, brand_label=brand_label, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
        return canvas

    # service-editorial and legacy fashion-editorial: image-led service layouts
    # with separate, bounded copy zones. The neutral alias prevents IT packages
    # from being mislabeled as fashion while retaining deterministic rendering.
    canvas = _draw_gradient_overlay(canvas, 0, 125)
    draw = ImageDraw.Draw(canvas, "RGBA")
    panel_right = int(size[0] * 0.57)
    panel_bottom = size[1] - margin // 2
    draw.rounded_rectangle((margin // 2, margin // 2, panel_right, panel_bottom), radius=26, fill=(*primary, 185))
    title_font, title, title_spacing = _fit_template_text(
        draw,
        headline or "Designed for your moment",
        typography,
        font_key="heading",
        max_width=panel_right - margin * 2,
        max_height=int(size[1] * 0.17),
        start_size=max(30, int(size[0] * 0.060)),
        min_size=24,
        spacing=5,
    )
    title_y = int(size[1] * 0.20)
    draw.multiline_text((margin, title_y), title, font=title_font, fill=surface, spacing=title_spacing)
    detail_font, detail, detail_spacing = _fit_template_text(
        draw,
        body or "Crafted details. Personal style.",
        typography,
        font_key="body",
        max_width=panel_right - margin * 2,
        max_height=int(size[1] * 0.15),
        start_size=max(24, int(size[0] * 0.036)),
        min_size=20,
        spacing=4,
    )
    detail_y = int(size[1] * 0.48)
    draw.multiline_text((margin, detail_y), detail, font=detail_font, fill=surface, spacing=detail_spacing)
    if cta:
        cta_font, cta_text, _ = _fit_template_text(
            draw,
            cta,
            typography,
            font_key="small",
            max_width=panel_right - margin * 2,
            max_height=34,
            start_size=max(18, int(size[0] * 0.020)),
            min_size=14,
            spacing=2,
        )
        cta_y = int(size[1] * 0.74)
        draw.rounded_rectangle((margin, cta_y - 24, panel_right - margin, cta_y + 24), radius=16, fill=accent)
        draw.text(((margin + panel_right - margin) // 2, cta_y), cta_text, font=cta_font, fill=primary, anchor="mm")
    canvas = _place_logo(canvas, logo, settings["logo_position"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_footer(draw, canvas, brand_label=brand_label, website=website, handle=handle, phone=phone, whatsapp=whatsapp, location=location, color=surface, accent=accent, font=small)
    return canvas



def _local_path(media: Media) -> str:
    path = Path(media.stored_path)
    if not path.exists():
        raise ValueError("Source media is not available in the local storage backend")
    return str(path)



def compose_generated_text_variants(
    db: Session,
    *,
    organization_id: int,
    user_id: int,
    theme_id: int | None = None,
    template_family: str = "quote-card",
    background_preset: str = "midnight-aurora",
    headline: str = "",
    body: str = "",
    cta: str = "",
    website: str | None = None,
    handle: str | None = None,
    phone: str | None = None,
    whatsapp: str | None = None,
    location: str | None = None,
) -> list[Media]:
    """Create branded text-card variants when generation has no source photo."""
    if template_family not in TEMPLATE_FAMILIES:
        raise ValueError(f"Unsupported template family: {template_family}")
    if background_preset not in QUOTE_BACKGROUND_PRESETS:
        raise ValueError(f"Unsupported quote background preset: {background_preset}")
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    theme = db.query(BrandTheme).filter(BrandTheme.id == theme_id, BrandTheme.organization_id == organization_id).first() if theme_id else None
    logo = None
    if profile and profile.logo_media_id:
        logo_media = db.query(Media).filter(Media.id == profile.logo_media_id, Media.organization_id == organization_id).first()
        if logo_media:
            logo = Image.open(_local_path(logo_media))
    settings = _theme_settings(profile, theme)
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    brand_label = organization.name if organization else None
    website = website or (profile.website_url if profile else None)
    phone = phone or (profile.contact_phone if profile else None)
    whatsapp = whatsapp or (profile.whatsapp_display_phone if profile else None)
    location = location or None
    variants: list[Media] = []
    for platform, size in FORMAT_SIZES.items():
        base = Image.new("RGB", size, settings["primary"])
        rendered = _render_template(
            base,
            size,
            family=template_family,
            background_preset=background_preset,
            headline=headline,
            body=body,
            cta=cta,
            website=website,
            handle=handle,
            phone=phone,
            whatsapp=whatsapp,
            location=location,
            brand_label=brand_label,
            logo=logo,
            settings=settings,
        )
        buffer = io.BytesIO()
        rendered.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        filename = f"{platform}-{template_family}-generated-{uuid.uuid4().hex}.png"
        upload = UploadFile(filename=filename, file=buffer, headers=Headers({"content-type": "image/png"}))
        variants.append(MediaService(db).save_upload(upload, user_id, organization_id))
    return variants


def compose_branded_variants(
    db: Session,
    *,
    organization_id: int,
    user_id: int,
    source_media_id: int,
    theme_id: int | None = None,
    template_family: str = "fashion-editorial",
    background_preset: str = "midnight-aurora",
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
    if background_preset not in QUOTE_BACKGROUND_PRESETS:
        raise ValueError(f"Unsupported quote background preset: {background_preset}")
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
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    brand_label = organization.name if organization else None
    website = website or (profile.website_url if profile else None)
    phone = phone or (profile.contact_phone if profile else None)
    whatsapp = whatsapp or (profile.whatsapp_display_phone if profile else None)
    location_values = _json(profile.locations_json, []) if profile else []
    location = location or (", ".join(str(item).strip() for item in location_values if str(item).strip()) if isinstance(location_values, list) else None)
    handle = handle or None
    variants: list[Media] = []
    with Image.open(_local_path(source)) as original:
        for platform, size in FORMAT_SIZES.items():
            rendered = _render_template(
                original,
                size,
                family=template_family,
                background_preset=background_preset,
                headline=headline,
                body=body,
                cta=cta,
                website=website,
                handle=handle,
                phone=phone,
                whatsapp=whatsapp,
                location=location,
                brand_label=brand_label,
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
