"""Safe social-listening and audience-intelligence persistence helpers."""

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content_opportunity import ContentOpportunity
from app.models.social_signal import SocialSignal
from app.models.workspace_intelligence import WorkspaceProfile


def _list_json(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()] if isinstance(parsed, list) else []


def _sentiment(text: str) -> tuple[str, float]:
    lowered = text.casefold()
    positive = sum(lowered.count(term) for term in ("growth", "success", "improve", "benefit", "launch", "win"))
    negative = sum(lowered.count(term) for term in ("fail", "fraud", "problem", "complaint", "risk", "loss"))
    if positive and negative:
        return "mixed", round((positive - negative) / max(1, positive + negative), 4)
    if positive:
        return "positive", 1.0
    if negative:
        return "negative", -1.0
    return "neutral", 0.0


def _signal_type(title: str, query: str | None, profile: WorkspaceProfile | None) -> str:
    text = f"{title} {query or ''}".casefold()
    competitors = [item.casefold() for item in _list_json(profile.competitor_urls_json)] if profile else []
    if any(item and item in text for item in competitors):
        return "competitor"
    if any(term in text for term in ("customer", "audience", "buyer", "user", "feedback")):
        return "audience"
    return "trend"


def _upsert(db: Session, organization_id: int, item: dict[str, Any]) -> SocialSignal:
    external_id = str(item.get("external_id") or item.get("source_url") or item["title"])[:1000]
    signal = (
        db.query(SocialSignal)
        .filter(
            SocialSignal.organization_id == organization_id,
            SocialSignal.source_type == item.get("source_type", "manual"),
            SocialSignal.external_id == external_id,
        )
        .first()
    )
    if signal is None:
        signal = SocialSignal(
            organization_id=organization_id,
            source_type=item.get("source_type", "manual"),
            external_id=external_id,
        )
        db.add(signal)
    title = str(item.get("title") or "Untitled signal").strip()
    excerpt = str(item.get("excerpt") or item.get("summary") or "").strip()
    sentiment, sentiment_score = _sentiment(f"{title} {excerpt}")
    signal.signal_type = item.get("signal_type", "trend")
    signal.source_url = item.get("source_url")
    signal.query = item.get("query")
    signal.subject = item.get("subject")
    signal.title = title[:1000]
    signal.excerpt = excerpt[:10000]
    signal.publisher = item.get("publisher")
    signal.published_at = item.get("published_at")
    signal.sentiment = item.get("sentiment", sentiment)
    signal.sentiment_score = item.get("sentiment_score", sentiment_score)
    signal.relevance_score = float(item.get("relevance_score", 0.0) or 0.0)
    signal.engagement_count = int(item.get("engagement_count", 0) or 0)
    signal.status = "new"
    signal.metadata_json = json.dumps(item.get("metadata") or {}, ensure_ascii=False)
    return signal


def collect_workspace_signals(db: Session, organization_id: int) -> list[SocialSignal]:
    """Convert source-grounded opportunities into reviewable intelligence signals."""
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    opportunities = (
        db.query(ContentOpportunity)
        .filter(ContentOpportunity.organization_id == organization_id)
        .order_by(ContentOpportunity.discovered_at.desc())
        .limit(100)
        .all()
    )
    signals = []
    for opportunity in opportunities:
        title = opportunity.title or ""
        signal = _upsert(
            db,
            organization_id,
            {
                "source_type": opportunity.source_type,
                "external_id": opportunity.external_id,
                "source_url": opportunity.source_url,
                "publisher": opportunity.publisher,
                "title": title,
                "summary": opportunity.summary,
                "published_at": opportunity.source_published_at,
                "relevance_score": opportunity.relevance_score,
                "signal_type": _signal_type(title, None, profile),
                "metadata": {"opportunity_id": opportunity.id, "trust_score": opportunity.trust_score},
            },
        )
        signals.append(signal)
    db.commit()
    for signal in signals:
        db.refresh(signal)
    return signals


def create_manual_signal(db: Session, organization_id: int, payload: dict[str, Any]) -> SocialSignal:
    """Persist an operator-supplied public signal; caller must enforce workspace membership."""
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    payload = dict(payload)
    payload.setdefault("signal_type", _signal_type(str(payload.get("title", "")), payload.get("query"), profile))
    payload.setdefault("source_type", "manual")
    signal = _upsert(db, organization_id, payload)
    db.commit()
    db.refresh(signal)
    return signal


def summarize_signals(db: Session, organization_id: int) -> dict[str, Any]:
    rows = db.query(SocialSignal).filter(SocialSignal.organization_id == organization_id, SocialSignal.status != "archived").all()
    sentiments = {key: sum(1 for row in rows if row.sentiment == key) for key in ("positive", "neutral", "negative", "mixed")}
    types = {key: sum(1 for row in rows if row.signal_type == key) for key in ("mention", "competitor", "audience", "trend")}
    return {
        "organization_id": organization_id,
        "signal_count": len(rows),
        "sentiments": sentiments,
        "signal_types": types,
        "average_relevance": round(sum(row.relevance_score for row in rows) / len(rows), 4) if rows else 0.0,
        "latest_published_at": max((row.published_at for row in rows if row.published_at), default=None),
    }
