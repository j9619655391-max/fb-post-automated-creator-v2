"""Regression tests for deterministic branded creative templates."""

from PIL import Image

from app.services.media_composer_service import FORMAT_SIZES, _render_template


def _settings():
    return {
        "primary": (15, 23, 42),
        "surface": (248, 250, 252),
        "accent": (250, 204, 21),
        "highlight": (236, 72, 153),
        "logo_position": "bottom-right",
        "background_style": "image",
        "typography": {},
    }


def test_all_template_families_render_platform_variants():
    original = Image.new("RGB", (900, 900), (120, 80, 60))
    for family in ("fashion-editorial", "product-catalog", "quote-card", "collection-story"):
        for size in FORMAT_SIZES.values():
            rendered = _render_template(
                original,
                size,
                family=family,
                headline="Kashvera Signature Suit",
                body="Crafted detail for your next occasion.",
                cta="Book a consultation",
                website="https://example.com",
                handle="@kashverafashion",
                phone="+91 90000 00000",
                whatsapp="+91 90000 00000",
                location="Delhi",
                logo=None,
                settings=_settings(),
            )
            assert rendered.size == size
            assert rendered.mode == "RGB"
            assert rendered.getbbox() is not None
