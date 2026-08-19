"""Models for Meta/Facebook OAuth (single App; user consent only)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class OAuthState(Base):
    """Temporary state for OAuth CSRF protection; expires after use or timeout."""
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(64), unique=True, nullable=False, index=True)
    provider = Column(String(32), nullable=False, default="facebook", server_default="facebook", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="oauth_states")


class MetaUserToken(Base):
    """Stored Meta user access token (encrypted at rest); one per user for MVP."""
    __tablename__ = "meta_user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    access_token_encrypted = Column(Text, nullable=False)
    meta_user_id = Column(String(64), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="meta_user_token")
