from datetime import datetime, timedelta, timezone

from app.models.content import Content, ContentStatus
from app.models.meta_page import MetaPage
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus
from app.models.user import User
from app.scheduler import schedule_facebook_post


def _approved_content_and_page(db):
    user = User(
        username="scheduler-user",
        email="scheduler-user@example.com",
        full_name="Scheduler User",
        hashed_password="not-used-in-this-test",
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.flush()

    content = Content(
        title="Scheduled content",
        body="Scheduled body",
        status=ContentStatus.APPROVED,
        created_by_id=user.id,
    )
    page = MetaPage(
        user_id=user.id,
        page_id="page-123",
        page_name="Test Page",
        access_token_encrypted="encrypted-token",
    )
    db.add_all([content, page])
    db.commit()
    db.refresh(content)
    db.refresh(page)
    return user, content, page


def test_schedule_rejects_past_time(db, monkeypatch):
    user, content, page = _approved_content_and_page(db)
    monkeypatch.setattr(
        "app.scheduler.publish_to_facebook_task.apply_async",
        lambda *args, **kwargs: None,
    )

    result = schedule_facebook_post(
        db,
        content_id=content.id,
        meta_page_id=page.id,
        publish_time=datetime.now(timezone.utc) - timedelta(minutes=1),
        user_id=user.id,
    )

    assert result is None
    assert db.query(ScheduledPost).count() == 0


def test_schedule_is_idempotent_for_same_content_page_time(db, monkeypatch):
    user, content, page = _approved_content_and_page(db)
    enqueue_calls = []
    monkeypatch.setattr(
        "app.scheduler.publish_to_facebook_task.apply_async",
        lambda *args, **kwargs: enqueue_calls.append((args, kwargs)),
    )
    scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)

    first = schedule_facebook_post(
        db,
        content_id=content.id,
        meta_page_id=page.id,
        publish_time=scheduled_time,
        user_id=user.id,
    )
    second = schedule_facebook_post(
        db,
        content_id=content.id,
        meta_page_id=page.id,
        publish_time=scheduled_time,
        user_id=user.id,
    )

    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert first.status == ScheduledPostStatus.PENDING
    assert db.query(ScheduledPost).count() == 1
    assert len(enqueue_calls) == 1
