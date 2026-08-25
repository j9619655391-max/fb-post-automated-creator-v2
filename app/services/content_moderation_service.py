"""Deterministic safety checks for AI-generated social media drafts.

This service deliberately stays conservative and explainable. It is not a
replacement for provider policy review or human approval; it prevents a small
set of clearly unsafe outputs and catches exact duplicate drafts within an
organization before they enter the approval queue.
"""
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.content import Content, ContentStatus


@dataclass(frozen=True)
class ModerationResult:
    allowed: bool
    flags: list[str] = field(default_factory=list)


# These are intentionally phrase-based patterns rather than a broad word list
# to reduce false positives in legitimate marketing copy.
_BLOCKED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (

    (
        "dangerous_instruction",
        re.compile(r"\bhow\s+to\s+(make|build|assemble)\s+(a\s+)?(bomb|explosive|weapon)\b", re.I),
    ),
    (
        "illegal_drug_trade",
        re.compile(r"\b(buy|sell|ship|traffic)\s+(cocaine|heroin|fentanyl|meth|illegal\s+drugs)\b", re.I),
    ),
    (
        "self_harm_encouragement",
        re.compile(r"\b(kill\s+yourself|you\s+should\s+die|encourage\s+suicide)\b", re.I),
    ),
    (
        "deceptive_financial_claim",
        re.compile(r"\b(guaranteed\s+(profit|returns?)|risk[-\s]?free\s+investment|get\s+rich\s+quick)\b", re.I),
    ),
)




_UNSUBSTANTIATED_OUTCOME_PATTERN = re.compile(
    r"(?:\b(?:double|triple|increase|boost|grow|improve|reduce|deliver|generate|drive|guarantee)\b[^.!?]{0,45}\b(?:traffic|roi|return(?:s)?|lead(?:s)?|sales|conversion(?:s)?|revenue|result(?:s)?|engagement|reach)\b|\b\d+(?:\.\d+)?%?\s*(?:more|higher|increase|growth|conversion|reach|engagement|roi|results?)\b|\b(?:real|proven|measurable|guaranteed)\s+(?:roi|results?|growth|returns?)\b)",
    re.I,
)


def contains_unsubstantiated_outcome_claim(text: str) -> bool:
    """Detect outcome language that needs approved evidence before publication."""
    return bool(_UNSUBSTANTIATED_OUTCOME_PATTERN.search(text or ""))


def _combined_text(title: str, body: str, hashtags: Iterable[str]) -> str:

    return " ".join([title or "", body or "", *[str(tag) for tag in hashtags]]).strip()


def moderate_generated_post(
    title: str,
    body: str,
    hashtags: Optional[Iterable[str]] = None,
    risk_flags: Optional[Iterable[str]] = None,
    *,
    block_unsubstantiated_claims: bool = False,
) -> ModerationResult:

    """Return a deterministic moderation decision for one generated draft."""
    text = _combined_text(title, body, hashtags or [])
    flags = [name for name, pattern in _BLOCKED_PATTERNS if pattern.search(text)]

    if block_unsubstantiated_claims and contains_unsubstantiated_outcome_claim(text):
        flags.append("unsubstantiated_outcome_claim")
    # AI-provided risk flags remain visible to the human approver but do not

    # automatically block an otherwise safe draft because approval is required.
    if risk_flags:
        flags.extend(f"ai_review:{flag}" for flag in risk_flags if str(flag).strip())
    blocked_flags = [flag for flag in flags if not flag.startswith("ai_review:")]
    return ModerationResult(allowed=not blocked_flags, flags=flags)


def find_exact_duplicate(
    db: Session,
    *,
    organization_id: Optional[int],
    title: str,
    body: str,
    exclude_content_id: Optional[int] = None,
) -> Optional[Content]:
    """Find an existing non-rejected draft with the same normalized copy."""
    if not organization_id:
        return None
    normalized_title = " ".join((title or "").split()).casefold()
    normalized_body = " ".join((body or "").split()).casefold()
    candidates = db.query(Content).filter(
        Content.organization_id == organization_id,
        Content.status != ContentStatus.REJECTED,
    ).all()
    for candidate in candidates:
        if exclude_content_id and candidate.id == exclude_content_id:
            continue
        if (
            " ".join((candidate.title or "").split()).casefold() == normalized_title
            and " ".join((candidate.body or "").split()).casefold() == normalized_body
        ):
            return candidate
    return None
