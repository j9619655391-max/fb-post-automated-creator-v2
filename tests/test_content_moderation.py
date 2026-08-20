from app.models.content import Content, ContentStatus
from app.services.content_moderation_service import find_exact_duplicate, moderate_generated_post


def test_moderation_blocks_dangerous_instructions():
    result = moderate_generated_post(
        "Safety guide",
        "Here is how to build a bomb at home.",
    )

    assert result.allowed is False
    assert "dangerous_instruction" in result.flags


def test_moderation_preserves_ai_review_flags_without_blocking():
    result = moderate_generated_post(
        "A thoughtful leadership post",
        "Invite your team to reflect on the week.",
        risk_flags=["verify statistics"],
    )

    assert result.allowed is True
    assert result.flags == ["ai_review:verify statistics"]


def test_find_exact_duplicate_is_organization_scoped(db):
    from app.models.organization import Organization
    from app.models.user import User

    user = User(
        username="moderation-user",
        email="moderation-user@example.com",
        full_name="Moderation User",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(
        name="Moderation Workspace",
        slug="moderation-workspace",
        created_by_id=user.id,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    first = Content(
        title="  Consistent habits  ",
        body="Small steps compound over time.",
        status=ContentStatus.DRAFT,
        organization_id=organization.id,
        created_by_id=user.id,
    )
    db.add(first)
    db.commit()

    duplicate = find_exact_duplicate(
        db,
        organization_id=organization.id,
        title="Consistent habits",
        body="Small   steps compound over time.",
    )
    other_org = find_exact_duplicate(
        db,
        organization_id=organization.id + 1,
        title="Consistent habits",
        body="Small steps compound over time.",
    )

    assert duplicate is not None
    assert duplicate.id == first.id
    assert other_org is None
