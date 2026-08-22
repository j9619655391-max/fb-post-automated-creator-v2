"""Publishing metric ingestion and explainable performance summaries."""

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.publishing_metric import PublishingMetric


_METRIC_FIELDS = (
    "impressions",
    "reach",
    "engagements",
    "reactions",
    "comments",
    "shares",
    "clicks",
    "video_views",
    "saves",
    "negative_feedback",
)


def _rate(engagements: int, reach: int) -> float:
    return round(engagements / max(1, reach), 6)


def ingest_metric(db: Session, organization_id: int, payload: dict[str, Any]) -> PublishingMetric:
    content = db.query(Content).filter(Content.id == payload["content_id"], Content.organization_id == organization_id).first()
    if content is None:
        raise ValueError("Content does not belong to this workspace")
    captured_at = payload["captured_at"]
    publish_status_id = payload.get("publish_status_id")
    metric = None
    if publish_status_id:
        metric = (
            db.query(PublishingMetric)
            .filter(PublishingMetric.publish_status_id == publish_status_id, PublishingMetric.captured_at == captured_at)
            .first()
        )
    if metric is None:
        metric = PublishingMetric(
            organization_id=organization_id,
            content_id=content.id,
            publish_status_id=publish_status_id,
            platform=payload["platform"],
            captured_at=captured_at,
        )
        db.add(metric)
    for field in _METRIC_FIELDS:
        setattr(metric, field, int(payload.get(field, 0) or 0))
    metric.platform_post_id = payload.get("platform_post_id")
    metric.source = payload.get("source", "manual")
    metric.raw_json = json.dumps(payload.get("raw") or {}, ensure_ascii=False)
    metric.engagement_rate = _rate(metric.engagements, metric.reach)
    db.commit()
    db.refresh(metric)
    return metric


def summarize_performance(db: Session, organization_id: int) -> dict[str, Any]:
    metrics = db.query(PublishingMetric).filter(PublishingMetric.organization_id == organization_id).all()
    totals = {field: sum(int(getattr(row, field) or 0) for row in metrics) for field in _METRIC_FIELDS}
    platform_rows: dict[str, list[PublishingMetric]] = defaultdict(list)
    for row in metrics:
        platform_rows[row.platform].append(row)
    by_platform: dict[str, dict[str, float | int]] = {}
    for platform, rows in platform_rows.items():
        reach = sum(row.reach for row in rows)
        engagements = sum(row.engagements for row in rows)
        by_platform[platform] = {
            "metric_count": len(rows),
            "impressions": sum(row.impressions for row in rows),
            "reach": reach,
            "engagements": engagements,
            "engagement_rate": _rate(engagements, reach),
        }
    content_rows = (
        db.query(Content.id, Content.title, Content.risk_tier, PublishingMetric.engagements, PublishingMetric.reach)
        .join(PublishingMetric, PublishingMetric.content_id == Content.id)
        .filter(Content.organization_id == organization_id)
        .all()
    )
    grouped: dict[int, dict[str, Any]] = {}
    for content_id, title, risk_tier, engagements, reach in content_rows:
        item = grouped.setdefault(content_id, {"content_id": content_id, "title": title, "risk_tier": risk_tier, "engagements": 0, "reach": 0})
        item["engagements"] += int(engagements or 0)
        item["reach"] += int(reach or 0)
    top_content = sorted(grouped.values(), key=lambda item: item["engagements"], reverse=True)[:10]
    return {"organization_id": organization_id, "metric_count": len(metrics), "totals": totals, "by_platform": by_platform, "top_content": top_content}
