import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content_opportunity import ContentOpportunity, OpportunityStatus
from app.models.workspace_intelligence import WorkspaceProfile, WorkspaceSource


class OpportunityDiscoveryError(ValueError):
    pass


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()] if isinstance(parsed, list) else []


def _query_terms(profile: WorkspaceProfile | None) -> list[str]:
    if not profile:
        return []
    terms = _json_list(profile.keywords_json)
    if profile.industry:
        terms.append(profile.industry)
    terms.extend(_json_list(profile.services_json)[:5])
    return list(dict.fromkeys(term for term in terms if term))[:12]


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def _score(title: str, summary: str, terms: list[str], trust_score: float, published_at: datetime | None) -> tuple[float, float, float]:
    text = f"{title} {summary}".lower()
    matched = sum(1 for term in terms if term.lower() in text)
    relevance = min(1.0, matched / max(1, min(4, len(terms)))) if terms else 0.35
    if published_at:
        age_days = max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 86400)
        freshness = max(0.0, min(1.0, 1.0 - age_days / 30.0))
    else:
        freshness = 0.35
    return round(freshness, 4), round(relevance, 4), trust_score


def _upsert_opportunity(db: Session, organization_id: int, item: dict[str, Any]) -> ContentOpportunity:
    external_id = item.get("external_id") or item.get("source_url") or item["title"]
    opportunity = (
        db.query(ContentOpportunity)
        .filter(
            ContentOpportunity.organization_id == organization_id,
            ContentOpportunity.source_type == item["source_type"],
            ContentOpportunity.external_id == external_id,
        )
        .first()
    )
    if opportunity is None:
        opportunity = ContentOpportunity(
            organization_id=organization_id,
            source_type=item["source_type"],
            external_id=external_id,
        )
        db.add(opportunity)
    opportunity.source_url = item.get("source_url")
    opportunity.publisher = item.get("publisher")
    opportunity.title = item["title"][:1000]
    opportunity.summary = (item.get("summary") or "")[:10000]
    opportunity.source_published_at = item.get("source_published_at")
    opportunity.freshness_score = item["freshness_score"]
    opportunity.relevance_score = item["relevance_score"]
    opportunity.trust_score = item["trust_score"]
    opportunity.status = OpportunityStatus.NEW
    opportunity.metadata_json = json.dumps(item.get("metadata") or {}, ensure_ascii=False)
    return opportunity


def _discover_rss(source: WorkspaceSource, terms: list[str]) -> list[dict[str, Any]]:
    if not source.url:
        return []
    with httpx.Client(timeout=settings.source_discovery_timeout_seconds, follow_redirects=True) as client:
        response = client.get(source.url)
        response.raise_for_status()
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as exc:
        raise OpportunityDiscoveryError(f"Invalid RSS/XML feed: {source.url}") from exc
    items = []
    for entry in list(root.findall(".//item")) + list(root.findall(".//{http://www.w3.org/2005/Atom}entry")):
        def text(*paths: str) -> str:
            for path in paths:
                node = entry.find(path)
                if node is not None and (node.text or "").strip():
                    return (node.text or "").strip()
            return ""
        title = text("title", "{http://www.w3.org/2005/Atom}title")
        link = text("link", "{http://www.w3.org/2005/Atom}link")
        if not link:
            link_node = entry.find("{http://www.w3.org/2005/Atom}link")
            link = (link_node.attrib.get("href") if link_node is not None else "") or ""
        summary = text("description", "summary", "{http://www.w3.org/2005/Atom}summary")
        published = _parse_date(text("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"))
        if not title or not link:
            continue
        freshness, relevance, trust = _score(title, summary, terms, 0.65, published)
        items.append({"source_type": "rss", "source_url": link, "external_id": link, "publisher": source.title or source.url, "title": title, "summary": re.sub(r"<[^>]+>", " ", summary), "source_published_at": published, "freshness_score": freshness, "relevance_score": relevance, "trust_score": trust, "metadata": {"feed_url": source.url}})
        if len(items) >= settings.rss_discovery_max_items_per_source:
            break
    return items


def _discover_news(terms: list[str]) -> list[dict[str, Any]]:
    if not settings.news_api_key or not terms:
        return []
    params = {"q": " OR ".join(terms[:5]), "apiKey": settings.news_api_key, "pageSize": settings.source_discovery_max_items, "sortBy": "publishedAt", "language": "en"}
    with httpx.Client(timeout=settings.source_discovery_timeout_seconds) as client:
        response = client.get(settings.news_api_base_url, params=params)
        response.raise_for_status()
    payload = response.json()
    items = []
    for article in payload.get("articles", []):
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        if not title or not url:
            continue
        published = _parse_date(article.get("publishedAt"))
        summary = article.get("description") or ""
        freshness, relevance, trust = _score(title, summary, terms, 0.70, published)
        items.append({"source_type": "news", "source_url": url, "external_id": url, "publisher": (article.get("source") or {}).get("name"), "title": title, "summary": summary, "source_published_at": published, "freshness_score": freshness, "relevance_score": relevance, "trust_score": trust, "metadata": {"author": article.get("author"), "image_url": article.get("urlToImage")}})
    return items


def _discover_research(terms: list[str]) -> list[dict[str, Any]]:
    if not terms:
        return []
    params = {"search": " ".join(terms[:5]), "per-page": settings.source_discovery_max_items, "sort": "publication_date:desc"}
    if settings.openalex_api_key:
        params["api_key"] = settings.openalex_api_key
    with httpx.Client(timeout=settings.source_discovery_timeout_seconds) as client:
        response = client.get(settings.openalex_api_base_url, params=params)
        response.raise_for_status()
    items = []
    for work in response.json().get("results", []):
        title = (work.get("title") or "").strip()
        if not title:
            continue
        url = work.get("doi") or work.get("id")
        published = _parse_date(work.get("publication_date"))
        summary = "Research work indexed by OpenAlex. Review the abstract and original DOI before using claims."
        freshness, relevance, trust = _score(title, summary, terms, 0.85, published)
        items.append({"source_type": "research", "source_url": url, "external_id": work.get("id") or url, "publisher": (work.get("primary_location") or {}).get("source", {}).get("display_name") if work.get("primary_location") else "OpenAlex", "title": title, "summary": summary, "source_published_at": published, "freshness_score": freshness, "relevance_score": relevance, "trust_score": trust, "metadata": {"doi": work.get("doi"), "open_access": work.get("open_access"), "openalex_id": work.get("id")}})
    return items


def discover_workspace_opportunities(db: Session, organization_id: int) -> list[ContentOpportunity]:
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    terms = _query_terms(profile)
    discovered: list[dict[str, Any]] = []
    for source in db.query(WorkspaceSource).filter(WorkspaceSource.organization_id == organization_id, WorkspaceSource.is_active.is_(True)).all():
        if source.source_type == "rss":
            discovered.extend(_discover_rss(source, terms))
    discovered.extend(_discover_news(terms))
    discovered.extend(_discover_research(terms))
    opportunities = [_upsert_opportunity(db, organization_id, item) for item in discovered]
    db.commit()
    for opportunity in opportunities:
        db.refresh(opportunity)
    return sorted(opportunities, key=lambda item: (item.relevance_score + item.freshness_score, item.discovered_at), reverse=True)
