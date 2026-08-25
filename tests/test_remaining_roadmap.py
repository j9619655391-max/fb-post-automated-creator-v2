"""Tests for social intelligence, analytics, and automation safeguards."""

from datetime import datetime, timezone

from app.models.content import Content
from app.models.content_opportunity import ContentOpportunity
from app.models.organization import Organization
from app.models.user import User
from app.services.performance_service import ingest_metric, summarize_performance
from app.services.risk_policy_service import assess_content_risk, autopilot_decision, get_or_create_policy
from app.services.social_listening_service import collect_workspace_signals, summarize_signals


def _workspace(db):
    user = User(username="roadmap-user", email="roadmap@example.com", hashed_password="x", is_admin=True)
    db.add(user)
    db.flush()
    org = Organization(name="Roadmap Workspace", slug="roadmap-workspace", created_by_id=user.id)
    db.add(org)
    db.flush()
    return user, org


def test_risk_scoring_and_conservative_autopilot_default(db):
    user, org = _workspace(db)
    content = Content(
        title="Guaranteed profit",
        body="Get rich quick with risk-free investment.",
        organization_id=org.id,
        created_by_id=user.id,
    )
    db.add(content)
    db.flush()
    assess_content_risk(content)
    db.commit()
    assert content.risk_tier == "critical"
    assert content.risk_score >= 80
    allowed, reason = autopilot_decision(db, org.id, content)
    assert allowed is False
    assert reason == "approval_required"


def test_signal_collection_and_summary_from_opportunity(db):
    user, org = _workspace(db)
    db.add(
        ContentOpportunity(
            organization_id=org.id,
            source_type="news",
            external_id="news-1",
            source_url="https://example.com/news-1",
            publisher="Example News",
            title="Industry growth improves customer outcomes",
            summary="A public research-backed trend.",
            source_published_at=datetime.now(timezone.utc),
            freshness_score=0.9,
            relevance_score=0.8,
            trust_score=0.7,
        )
    )
    db.commit()
    signals = collect_workspace_signals(db, org.id)
    assert len(signals) == 1
    assert signals[0].signal_type == "audience"
    summary = summarize_signals(db, org.id)
    assert summary["signal_count"] == 1
    assert summary["sentiments"]["positive"] == 1


def test_metric_ingestion_and_summary(db):
    user, org = _workspace(db)
    content = Content(title="Launch", body="A product update.", organization_id=org.id, created_by_id=user.id)
    db.add(content)
    db.flush()
    metric = ingest_metric(
        db,
        org.id,
        {
            "content_id": content.id,
            "platform": "linkedin",
            "captured_at": datetime.now(timezone.utc),
            "reach": 100,
            "engagements": 12,
            "impressions": 150,
            "source": "manual",
            "raw": {"verified": True},
        },
    )
    assert metric.engagement_rate == 0.12
    summary = summarize_performance(db, org.id)
    assert summary["metric_count"] == 1
    assert summary["by_platform"]["linkedin"]["engagement_rate"] == 0.12
    assert summary["top_content"][0]["content_id"] == content.id
