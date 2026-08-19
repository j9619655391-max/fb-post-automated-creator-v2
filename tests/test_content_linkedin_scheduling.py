from datetime import datetime, timedelta, timezone

from app.models.content import ContentStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.scheduled_post import ScheduledPlatform
from app.models.user import User
from app.schemas.content import ContentApprovalRequest, ContentCreate
from app.services.content_service import ContentService


def test_inline_linkedin_schedule_is_preserved_and_enqueued(db, monkeypatch):
    user = User(
        username="linkedin-scheduler",
        email="linkedin-scheduler@example.com",
        full_name="LinkedIn Scheduler",
        hashed_password="not-a-real-password-hash",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    account = LinkedInAccount(
        user_id=user.id,
        linkedin_id="urn:li:person:test-scheduler",
        name="Test LinkedIn Profile",
        account_type="person",
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)
    service = ContentService(db)
    content = service.create_content(
        ContentCreate(
            title="LinkedIn scheduled draft",
            body="Approval-required LinkedIn content.",
            schedule_at=scheduled_at,
            schedule_platform="linkedin",
            schedule_linkedin_account_id=account.id,
        ),
        user.id,
    )

    assert content.schedule_platform == ScheduledPlatform.LINKEDIN
    assert content.schedule_linkedin_account_id == account.id
    assert content.schedule_meta_page_id is None

    service.submit_for_approval(content.id, user.id)
    calls = []
    monkeypatch.setattr(
        "app.scheduler.schedule_post",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    approved = service.approve_content(
        content.id,
        ContentApprovalRequest(approved=True, comment="Approved for LinkedIn"),
        user.id,
    )

    assert approved is not None
    assert approved.status == ContentStatus.APPROVED
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["platform"] == ScheduledPlatform.LINKEDIN
    assert kwargs["linkedin_account_id"] == account.id
    assert kwargs["meta_page_id"] is None


def test_inline_schedule_rejects_mixed_meta_and_linkedin_targets():
    from pytest import raises

    future = datetime.now(timezone.utc) + timedelta(hours=1)
    with raises(ValueError, match="exactly one LinkedIn account"):
        ContentService._normalize_schedule_platform(
            ContentCreate(
                title="Invalid target mix",
                body="This must be rejected.",
                schedule_at=future,
                schedule_platform="linkedin",
                schedule_meta_page_id=1,
                schedule_linkedin_account_id=2,
            )
        )
