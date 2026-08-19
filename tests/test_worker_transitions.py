from datetime import datetime, timedelta, timezone

import pytest
from celery.exceptions import Retry

from app.models.content import Content, ContentStatus
from app.models.meta_page import MetaPage
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus
from app.models.user import User
from app import scheduler


def _scheduled_post(db):
    user = User(
        username="worker-user",
        email="worker@example.com",
        full_name="Worker User",
        hashed_password="hashed",
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    content = Content(
        title="Worker test",
        body="Worker test body",
        status=ContentStatus.APPROVED,
        created_by_id=user.id,
    )
    page = MetaPage(
        user_id=user.id,
        page_id="worker-page",
        page_name="Worker Page",
        access_token_encrypted="encrypted",
    )
    db.add_all([content, page])
    db.flush()
    scheduled = ScheduledPost(
        content_id=content.id,
        meta_page_id=page.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        status=ScheduledPostStatus.PENDING,
    )
    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)
    return scheduled


def test_worker_marks_rate_limit_as_retrying(db, monkeypatch):
    scheduled = _scheduled_post(db)
    scheduled_id = scheduled.id
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db)

    def fail_publish(*args, **kwargs):
        raise RuntimeError("429 rate limit exceeded")

    monkeypatch.setattr("app.services.fb_api.publish_to_facebook", fail_publish)

    def capture_retry(*, exc, countdown):
        assert "rate limit" in str(exc).lower()
        assert countdown == 1
        raise Retry()

    monkeypatch.setattr(scheduler.publish_to_facebook_task, "retry", capture_retry)

    with pytest.raises(Retry):
        scheduler.publish_to_facebook_task.run(scheduled_id)

    db.expire_all()
    refreshed = db.query(ScheduledPost).get(scheduled_id)
    assert refreshed.status == ScheduledPostStatus.RETRYING
    assert refreshed.last_error_code == "RATE_LIMIT"
    assert refreshed.attempt_count == 1
    assert refreshed.next_retry_at is not None


def test_worker_dead_letters_after_retry_budget(db, monkeypatch):
    scheduled = _scheduled_post(db)
    scheduled_id = scheduled.id
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db)

    def fail_publish(*args, **kwargs):
        raise RuntimeError("network timeout")

    monkeypatch.setattr("app.services.fb_api.publish_to_facebook", fail_publish)
    monkeypatch.setattr(scheduler.publish_to_facebook_task, "max_retries", 0)

    result = scheduler.publish_to_facebook_task.run(scheduled_id)

    db.expire_all()
    refreshed = db.query(ScheduledPost).get(scheduled_id)
    assert result["status"] == "dead_letter"
    assert refreshed.status == ScheduledPostStatus.DEAD_LETTER
    assert refreshed.last_error_code == "NETWORK_ERROR"
    assert refreshed.completed_at is not None
    assert refreshed.next_retry_at is None
