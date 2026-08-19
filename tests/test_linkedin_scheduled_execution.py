from datetime import datetime, timedelta, timezone

from app.models.content import Content, ContentStatus
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.models.linkedin_account import LinkedInAccount
from app.models.scheduled_post import ScheduledPlatform, ScheduledPost, ScheduledPostStatus
from app.models.user import User
from app import scheduler


def _linkedin_scheduled_post(db):
    user = User(
        username="linkedin-scheduler-user",
        email="linkedin-scheduler@example.com",
        full_name="LinkedIn Scheduler User",
        hashed_password="hashed",
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    content = Content(
        title="LinkedIn scheduled test",
        body="Scheduled LinkedIn body",
        status=ContentStatus.APPROVED,
        created_by_id=user.id,
    )
    account = LinkedInAccount(
        user_id=user.id,
        linkedin_id="urn:li:person:test",
        name="LinkedIn Test Account",
        account_type="person",
    )
    db.add_all([content, account])
    db.flush()
    scheduled = ScheduledPost(
        content_id=content.id,
        platform=ScheduledPlatform.LINKEDIN,
        linkedin_account_id=account.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        status=ScheduledPostStatus.PENDING,
    )
    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)
    return scheduled.id, content.id, account.id, user.id


def test_linkedin_scheduled_execution_posts(db, monkeypatch):
    scheduled_id, content_id, account_id, user_id = _linkedin_scheduled_post(db)
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db)

    def fake_publish(db, content_id, linkedin_account_ids, user_id):
        db.add(ContentPublishStatus(
            content_id=content_id,
            linkedin_account_id=linkedin_account_ids[0],
            status=PublishStatusEnum.POSTED,
            platform_post_id="urn:li:share:test",
        ))
        db.commit()

    monkeypatch.setattr("app.services.linkedin_api.publish_to_linkedin", fake_publish)
    result = scheduler.publish_scheduled_post_task.run(scheduled_id)

    db.expire_all()
    scheduled = db.get(ScheduledPost, scheduled_id)
    assert result["status"] == "posted"
    assert scheduled.status == ScheduledPostStatus.POSTED
    assert scheduled.platform == ScheduledPlatform.LINKEDIN
    assert scheduled.linkedin_account_id == account_id


def test_linkedin_scheduled_auth_failure_is_terminal(db, monkeypatch):
    scheduled_id, content_id, account_id, user_id = _linkedin_scheduled_post(db)
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db)

    def fake_publish(db, content_id, linkedin_account_ids, user_id):
        db.add(ContentPublishStatus(
            content_id=content_id,
            linkedin_account_id=linkedin_account_ids[0],
            status=PublishStatusEnum.FAILED,
            error_message="AUTH_REQUIRED: LinkedIn connection expired",
        ))
        db.commit()

    monkeypatch.setattr("app.services.linkedin_api.publish_to_linkedin", fake_publish)
    result = scheduler.publish_scheduled_post_task.run(scheduled_id)

    db.expire_all()
    scheduled = db.get(ScheduledPost, scheduled_id)
    assert result["status"] == "failed"
    assert scheduled.status == ScheduledPostStatus.FAILED
    assert scheduled.last_error_code == "AUTH_REQUIRED"
