"""Safe refresh and normalization for workspace intelligence sources."""
import ipaddress
import json
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.workspace_intelligence import WorkspaceSource


MAX_RESPONSE_BYTES = 2_000_000
MAX_TEXT_CHARS = 100_000
REQUEST_TIMEOUT_SECONDS = 12
FETCH_USER_AGENT = "AutoGrowthWorkspaceSourceBot/1.0 (+local-business-intelligence)"


class WorkspaceSourceRefreshError(ValueError):
    """Raised when a source cannot be safely refreshed."""


def _validate_public_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise WorkspaceSourceRefreshError("Only public http(s) URLs can be refreshed")
    if parsed.username or parsed.password:
        raise WorkspaceSourceRefreshError("Source URLs must not contain credentials")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
        raise WorkspaceSourceRefreshError("Localhost sources are not allowed")
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise WorkspaceSourceRefreshError("Source hostname could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise WorkspaceSourceRefreshError("Private or reserved network sources are not allowed")
    return parsed.geturl(), hostname


def _allowed_by_robots(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        # A missing/unreachable robots file is not treated as permission to crawl
        # broadly; the user explicitly supplied this exact URL, so permit one fetch.
        return True
    return parser.can_fetch(user_agent, url)


def _extract_document(url: str, response: requests.Response) -> tuple[str, str, dict[str, object]]:
    content_type = (response.headers.get("content-type") or "").lower()
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise WorkspaceSourceRefreshError("Website source must return HTML")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise WorkspaceSourceRefreshError("Website source response is too large")

    soup = BeautifulSoup(response.content, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        element.decompose()
    title = (soup.title.get_text(" ", strip=True) if soup.title else "")[:500]
    description_tag = soup.find("meta", attrs={"name": lambda value: value and value.lower() == "description"})
    description = (description_tag.get("content", "") if description_tag else "")[:2000]
    root = soup.find("main") or soup.body or soup
    text = " ".join(root.get_text(" ", strip=True).split())[:MAX_TEXT_CHARS]
    if not text:
        raise WorkspaceSourceRefreshError("Website source did not contain readable text")
    metadata = {
        "canonical_url": url,
        "content_type": content_type,
        "http_status": response.status_code,
        "title": title,
        "meta_description": description,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    return title, text, metadata


def refresh_website_source(db: Session, source: WorkspaceSource) -> WorkspaceSource:
    if source.source_type != "website" or not source.url:
        raise WorkspaceSourceRefreshError("Only website sources can be refreshed automatically")
    url, hostname = _validate_public_url(source.url)
    if not _allowed_by_robots(url, FETCH_USER_AGENT):
        raise WorkspaceSourceRefreshError("robots.txt does not allow this source fetch")

    response = requests.get(
        url,
        headers={"User-Agent": FETCH_USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        timeout=REQUEST_TIMEOUT_SECONDS,
        allow_redirects=True,
    )
    response.raise_for_status()
    final_url, final_hostname = _validate_public_url(response.url)
    if final_hostname != hostname and not final_hostname.endswith(f".{hostname}"):
        raise WorkspaceSourceRefreshError("Redirected source leaves the supplied site")
    title, text, metadata = _extract_document(final_url, response)
    source.title = title or source.title
    source.content_text = text
    source.excerpt = text[:1200]
    source.metadata_json = json.dumps(metadata, ensure_ascii=False)
    source.last_fetched_at = datetime.now(timezone.utc)
    source.trust_level = "user_supplied"
    source.review_status = "pending"
    db.commit()
    db.refresh(source)
    return source


def refresh_workspace_web_sources(db: Session, organization_id: int) -> tuple[list[WorkspaceSource], list[str]]:
    sources = (
        db.query(WorkspaceSource)
        .filter(
            WorkspaceSource.organization_id == organization_id,
            WorkspaceSource.source_type == "website",
            WorkspaceSource.is_active.is_(True),
        )
        .order_by(WorkspaceSource.created_at.asc())
        .all()
    )
    refreshed: list[WorkspaceSource] = []
    errors: list[str] = []
    for source in sources:
        try:
            refreshed.append(refresh_website_source(db, source))
        except Exception as exc:
            db.rollback()
            errors.append(f"source_id={source.id}: {str(exc)[:300]}")
    return refreshed, errors
