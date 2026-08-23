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


def test_quote_background_presets_are_distinct_and_fit_long_hinglish_copy():
    from hashlib import sha256
    from app.services.media_composer_service import QUOTE_BACKGROUND_PRESETS

    original = Image.new("RGB", (1200, 800), (120, 80, 60))
    signatures = set()
    for preset in QUOTE_BACKGROUND_PRESETS:
        rendered = _render_template(
            original,
            (1200, 630),
            family="quote-card",
            background_preset=preset,
            headline="Sach Se Bhaagna Nahi",
            body="Jo dil ko sach lagta hai, usey kehne ki himmat rakho. Apna sach likho aur share karo!",
            cta="Agar dil ko laga, share karo.",
            website=None,
            handle=None,
            phone=None,
            whatsapp=None,
            location=None,
            brand_label="Love, Truth, Motivational, Pain Quotes",
            logo=None,
            settings=_settings(),
        )
        signatures.add(sha256(rendered.tobytes()).hexdigest())
        assert rendered.size == (1200, 630)
        assert rendered.mode == "RGB"
        assert rendered.getbbox() is not None

    assert len(signatures) == len(QUOTE_BACKGROUND_PRESETS)
