import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Content, ContentStatus
from app.models.content_revision import ContentRevision, TelegramApprovalRequest
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.workspace_intelligence import WorkspaceProfile
from app.schemas.content import ContentApprovalRequest

logger = logging.getLogger(__name__)


class TelegramApprovalError(ValueError):
    pass


def _api_url(method: str) -> str:
    if not settings.telegram_bot_token:
        raise TelegramApprovalError("Telegram bot token is not configured")
    return f"{settings.telegram_api_base_url.rstrip('/')}/bot{settings.telegram_bot_token}/{method}"


def _call_telegram(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=settings.telegram_request_timeout_seconds) as client:
        response = client.post(_api_url(method), json=payload)
        response.raise_for_status()
        body = response.json()
    if not body.get("ok"):
        raise TelegramApprovalError(str(body.get("description") or "Telegram API request failed"))
    return body.get("result") or {}


def _authorized_profile(db: Session, content: Content) -> WorkspaceProfile | None:
    if not content.organization_id:
        return None
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == content.organization_id).first()
    if not profile or not profile.telegram_approval_enabled or not profile.telegram_approval_chat_id:
        return None
    return profile


def _owner_id(db: Session, organization_id: int, fallback: int) -> int:
    owner = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.role == OrganizationRole.OWNER,
    ).first()
    return owner.user_id if owner else fallback


def _approval_text(content: Content, revision_number: int | None = None) -> str:
    revision = f"Revision {revision_number}" if revision_number else "Initial draft"
    body = (content.body or "").strip()
    return (
        f"Workspace content approval\n\n"
        f"Content ID: {content.id}\n"
        f"{revision}\n"
        f"Title: {content.title}\n\n"
        f"{body[:3500]}\n\n"
        f"Choose Accept or Reject. For rejection, press Reject and reply with your note."
    )


def send_approval_request(db: Session, content_id: int) -> TelegramApprovalRequest | None:
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content or content.status not in {ContentStatus.DRAFT, ContentStatus.PENDING_APPROVAL}:
        return None
    profile = _authorized_profile(db, content)
    if not profile:
        return None
    existing = db.query(TelegramApprovalRequest).filter(
        TelegramApprovalRequest.content_id == content.id,
        TelegramApprovalRequest.status.in_(["pending", "awaiting_note"]),
    ).first()
    if existing:
        return existing
    if content.status == ContentStatus.DRAFT:
        content.status = ContentStatus.PENDING_APPROVAL
    request = TelegramApprovalRequest(
        organization_id=content.organization_id,
        content_id=content.id,
        chat_id=str(profile.telegram_approval_chat_id),
        approver_user_id=str(profile.telegram_approval_user_id) if profile.telegram_approval_user_id else None,
        status="pending",
    )
    db.add(request)
    db.flush()
    try:
        result = _call_telegram(
            "sendMessage",
            {
                "chat_id": request.chat_id,
                "text": _approval_text(content),
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "Accept", "callback_data": f"approve:{request.id}"},
                        {"text": "Reject", "callback_data": f"reject:{request.id}"},
                    ]]
                },
            },
        )
    except Exception:
        db.rollback()
        logger.exception("telegram.approval_delivery_failed", extra={"content_id": content.id})
        raise
    request.telegram_message_id = str(result.get("message_id")) if result.get("message_id") is not None else None
    db.commit()
    db.refresh(request)
    return request


def _find_request(db: Session, request_id: int) -> TelegramApprovalRequest | None:
    return db.query(TelegramApprovalRequest).filter(TelegramApprovalRequest.id == request_id).first()


def _verify_chat_and_user(db: Session, request: TelegramApprovalRequest, chat_id: str, user_id: str | None) -> bool:
    if str(request.chat_id) != str(chat_id):
        return False
    if request.approver_user_id and user_id and str(request.approver_user_id) != str(user_id):
        return False
    return True


def _answer_callback(callback_id: str, text: str) -> None:
    try:
        _call_telegram("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": False})
    except Exception:
        logger.exception("telegram.callback_ack_failed")


def _reply(chat_id: str, text: str, reply_to: str | None = None) -> None:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = int(reply_to)
    _call_telegram("sendMessage", payload)


def handle_telegram_update(db: Session, update: dict[str, Any]) -> dict[str, Any]:
    callback = update.get("callback_query")
    if callback:
        data = str(callback.get("data") or "")
        action, _, raw_id = data.partition(":")
        if action not in {"approve", "reject"} or not raw_id.isdigit():
            return {"handled": False, "reason": "unsupported_callback"}
        request = _find_request(db, int(raw_id))
        message = callback.get("message") or {}
        chat_id = str((message.get("chat") or {}).get("id") or "")
        telegram_user_id = str((callback.get("from") or {}).get("id") or "")
        if not request or request.status not in {"pending", "awaiting_note"} or not _verify_chat_and_user(db, request, chat_id, telegram_user_id):
            _answer_callback(str(callback.get("id") or ""), "This approval request is no longer valid")
            return {"handled": False, "reason": "unauthorized_or_expired"}
        if action == "reject":
            request.status = "awaiting_note"
            request.last_update_id = str(update.get("update_id"))
            db.commit()
            _reply(request.chat_id, "Please reply to this message with the revision note. Example: make the tone more professional and shorten the CTA.", request.telegram_message_id)
            _answer_callback(str(callback.get("id") or ""), "Reply with your revision note")
            return {"handled": True, "action": "awaiting_note", "request_id": request.id}
        from app.services.content_service import ContentService
        content = db.query(Content).filter(Content.id == request.content_id).first()
        if not content:
            _answer_callback(str(callback.get("id") or ""), "Content no longer exists")
            return {"handled": False, "reason": "content_missing"}
        approver_id = _owner_id(db, request.organization_id, content.created_by_id)
        ContentService(db).approve_content(content.id, ContentApprovalRequest(approved=True), approver_id)
        request.status = "approved"
        request.last_update_id = str(update.get("update_id"))
        request.decided_at = datetime.now(timezone.utc)
        db.commit()
        _answer_callback(str(callback.get("id") or ""), "Approved")
        return {"handled": True, "action": "approved", "request_id": request.id, "content_id": content.id}

    message = update.get("message") or {}
    text = str(message.get("text") or "").strip()
    reply = message.get("reply_to_message") or {}
    replied_message_id = str(reply.get("message_id") or "")
    if not text or not replied_message_id:
        return {"handled": False, "reason": "not_a_revision_reply"}
    chat_id = str((message.get("chat") or {}).get("id") or "")
    telegram_user_id = str((message.get("from") or {}).get("id") or "")
    request = db.query(TelegramApprovalRequest).filter(
        TelegramApprovalRequest.telegram_message_id == replied_message_id,
        TelegramApprovalRequest.status == "awaiting_note",
    ).first()
    if not request or not _verify_chat_and_user(db, request, chat_id, telegram_user_id):
        return {"handled": False, "reason": "revision_request_not_found"}
    content = db.query(Content).filter(Content.id == request.content_id).first()
    if not content:
        return {"handled": False, "reason": "content_missing"}
    request.rejection_note = text[:10000]
    request.status = "rejected"
    request.last_update_id = str(update.get("update_id"))
    request.decided_at = datetime.now(timezone.utc)
    approver_id = _owner_id(db, request.organization_id, content.created_by_id)
    from app.services.content_service import ContentService
    ContentService(db).approve_content(content.id, ContentApprovalRequest(approved=False, comment=text), approver_id)
    db.commit()

    from app.services.content_generation_service import generate_and_persist_draft
    job = generate_and_persist_draft(
        db,
        content.created_by_id,
        category_name=f"Revision of {content.title}",
        extra_instruction=f"Revision feedback from the approver: {text}\nPrevious draft title: {content.title}\nPrevious draft body: {content.body}",
        organization_id=content.organization_id,
        idempotency_key=f"telegram-revision:{content.id}:{request.id}:{hash(text)}",
    )
    revised = job.content
    if revised:
        revision_count = db.query(ContentRevision).filter(ContentRevision.parent_content_id == content.id).count() + 1
        db.add(ContentRevision(organization_id=content.organization_id, parent_content_id=content.id, revised_content_id=revised.id, revision_number=revision_count, feedback_note=text, created_by_id=content.created_by_id))
        db.commit()
        send_approval_request(db, revised.id)
        _reply(chat_id, f"Revision {revision_count} is ready for approval.", replied_message_id)
        return {"handled": True, "action": "revised", "parent_content_id": content.id, "revised_content_id": revised.id}
    return {"handled": True, "action": "rejected", "content_id": content.id}


def poll_telegram_updates(db: Session, offset: int | None = None) -> dict[str, Any]:
    if not settings.telegram_bot_token:
        return {"enabled": False, "processed": 0, "next_offset": offset}
    params = {"timeout": settings.telegram_poll_timeout_seconds, "allowed_updates": json.dumps(["callback_query", "message"])}
    if offset is not None:
        params["offset"] = offset
    with httpx.Client(timeout=settings.telegram_request_timeout_seconds + settings.telegram_poll_timeout_seconds) as client:
        response = client.get(_api_url("getUpdates"), params=params)
        response.raise_for_status()
        body = response.json()
    if not body.get("ok"):
        raise TelegramApprovalError(str(body.get("description") or "Telegram polling failed"))
    processed = 0
    next_offset = offset
    for update in body.get("result", []):
        next_offset = int(update.get("update_id", 0)) + 1
        handle_telegram_update(db, update)
        processed += 1
    return {"enabled": True, "processed": processed, "next_offset": next_offset}
