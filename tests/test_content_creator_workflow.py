from app.models.content import Content, ContentStatus
from app.models.organization import Organization
from app.models.workspace_intelligence import WorkspaceProfile
from app.services.content_package_service import create_content_packages
from app.services import telegram_approval_service


def _workspace(db):
    from app.models.user import User

    user = User(username="creator", email="creator@example.com", hashed_password="hashed")
    db.add(user)
    db.flush()
    organization = Organization(name="Creator Workspace", slug="creator-workspace", created_by_id=user.id)
    db.add(organization)
    db.flush()
    return user, organization


def test_content_packages_create_platform_variants(db):
    user, organization = _workspace(db)
    content = Content(
        title="Fresh business insight",
        body="A practical insight for the audience.",
        organization_id=organization.id,
        created_by_id=user.id,
        status=ContentStatus.DRAFT,
    )
    db.add(content)
    db.commit()

    packages = create_content_packages(
        db,
        content.id,
        organization.id,
        ["facebook", "instagram", "linkedin"],
    )

    assert {package.platform for package in packages} == {"facebook", "instagram", "linkedin"}
    assert all(package.caption for package in packages)
    assert any("Share this" in package.caption for package in packages if package.platform == "instagram")


def test_telegram_approval_delivery_is_idempotent_and_approval_required(db, monkeypatch):
    user, organization = _workspace(db)
    profile = WorkspaceProfile(
        organization_id=organization.id,
        telegram_approval_enabled=True,
        telegram_approval_chat_id="-100123",
        approval_required=True,
    )
    content = Content(
        title="Approval draft",
        body="Draft body",
        organization_id=organization.id,
        created_by_id=user.id,
        status=ContentStatus.DRAFT,
    )
    db.add_all([profile, content])
    db.commit()
    monkeypatch.setattr(telegram_approval_service.settings, "telegram_bot_token", "test-token")
    calls = []

    def fake_call(method, payload):
        calls.append((method, payload))
        return {"message_id": 77}

    monkeypatch.setattr(telegram_approval_service, "_call_telegram", fake_call)
    first = telegram_approval_service.send_approval_request(db, content.id)
    second = telegram_approval_service.send_approval_request(db, content.id)

    assert first is not None
    assert second.id == first.id
    assert content.status == ContentStatus.PENDING_APPROVAL
    assert len(calls) == 1
    assert "Accept" in str(calls[0][1]["reply_markup"])
