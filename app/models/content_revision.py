from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentRevision(Base):
    __tablename__ = "content_revisions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    parent_content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    revised_content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False, default=1)
    feedback_note = Column(Text, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization")
    parent_content = relationship("Content", foreign_keys=[parent_content_id])
    revised_content = relationship("Content", foreign_keys=[revised_content_id])

    __table_args__ = (
        UniqueConstraint("revised_content_id", name="uq_content_revisions_revised_content"),
    )


class TelegramApprovalRequest(Base):
    __tablename__ = "telegram_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id = Column(String(255), nullable=False)
    approver_user_id = Column(String(255), nullable=True)
    telegram_message_id = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, default="pending", index=True)
    rejection_note = Column(Text, nullable=True)
    last_update_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    content = relationship("Content")
