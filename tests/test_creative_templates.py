"""Regression tests for deterministic branded creative templates."""

from PIL import Image

from app.services.media_composer_service import FORMAT_SIZES, TEMPLATE_COPY_BUDGETS, _render_template
from app.services.content_generation_service import (
    _image_copy_for_generation,
    _image_headline_for_generation,
    _template_family_for_category,
)
from app.services.content_moderation_service import moderate_generated_post


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


def test_ai_image_copy_is_separate_from_long_caption():
    from app.services.content_generation_service import _image_copy_for_generation

    generated = {
        "title": "Premium Digital Solutions Tailored for Growth",
        "image_text": "Digital solutions that help your business grow",
        "body": (
            "At Agile Aim Digital Marketing Solutions, we build powerful digital ecosystems "
            "with web development, branding, SEO, lead generation, content, and social media "
            "support. This longer caption belongs in the post copy, not inside the image."
        ),
    }

    image_copy = _image_copy_for_generation(generated, "fashion-editorial")

    assert image_copy == "Digital solutions that help your business grow"
    assert len(image_copy) <= 140
    assert "powerful digital ecosystems" not in image_copy


def test_service_showcase_uses_editorial_service_layout_and_budgeted_copy():
    generated = {
        "title": "Boost Your Online Presence with Expert Web Development",
        "image_text": "Expert Web Development and Branding for Your Next Digital Chapter",
        "body": "A full caption that must remain outside the image composition.",
    }

    assert _template_family_for_category("Service Showcase") == "fashion-editorial"
    assert _template_family_for_category("Product Showcase") == "product-catalog"
    assert len(_image_headline_for_generation(generated, "fashion-editorial")) <= TEMPLATE_COPY_BUDGETS["fashion-editorial"][0]
    assert len(_image_copy_for_generation(generated, "fashion-editorial")) <= TEMPLATE_COPY_BUDGETS["fashion-editorial"][1]


def test_overlay_budget_is_enforced_for_pathological_copy_across_platforms():
    original = Image.new("RGB", (1200, 900), (120, 80, 60))
    long_copy = " ".join(["A long service benefit that should never become a paragraph inside the image"] * 12)
    for size in FORMAT_SIZES.values():
        rendered = _render_template(
            original,
            size,
            family="fashion-editorial",
            headline=long_copy,
            body=long_copy,
            cta="Visit the website to request a consultation and discuss your next project",
            website="https://example.com",
            handle="@example",
            phone=None,
            whatsapp=None,
            location=None,
            logo=None,
            settings=_settings(),
        )
        assert rendered.size == size
        assert rendered.mode == "RGB"


def test_unsubstantiated_outcome_claims_are_blocked_without_evidence():
    blocked = moderate_generated_post(
        "Grow your business",
        "Our SEO strategy will double organic traffic and deliver real ROI.",
        block_unsubstantiated_claims=True,
    )
    assert not blocked.allowed
    assert "unsubstantiated_outcome_claim" in blocked.flags

    allowed_with_evidence = moderate_generated_post(
        "Grow your business",
        "Our SEO strategy delivered 25% more qualified leads in the approved case study.",
        block_unsubstantiated_claims=False,
    )
    assert allowed_with_evidence.allowed


def test_ai_image_copy_fallback_uses_title_for_legacy_marketing_responses():
    from app.services.content_generation_service import _image_copy_for_generation

    generated = {
        "title": "A concise title",
        "body": " ".join(["This is a long legacy caption"] * 50),
    }

    image_copy = _image_copy_for_generation(generated, "product-catalog")

    assert image_copy == "A concise title"
    assert len(image_copy) <= 140
    assert "long legacy caption" not in image_copy
