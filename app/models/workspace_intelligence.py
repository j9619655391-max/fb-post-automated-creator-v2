"""Workspace business intelligence profile and source records."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class WorkspaceProfile(Base):
    """Structured, organization-owned business context used by content generation."""

    __tablename__ = "workspace_profiles"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    business_description = Column(Text, nullable=True)
    mission = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)
    services_json = Column(Text, nullable=True)
    products_json = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    locations_json = Column(Text, nullable=True)
    brand_voice = Column(Text, nullable=True)
    tone = Column(String(100), nullable=True)
    visual_style = Column(Text, nullable=True)
    brand_colors_json = Column(Text, nullable=True)
    font_preferences_json = Column(Text, nullable=True)
    preferred_content_formats_json = Column(Text, nullable=True)
    content_cadence_json = Column(Text, nullable=True)
    keywords_json = Column(Text, nullable=True)
    preferred_languages_json = Column(Text, nullable=True)
    contact_email = Column(String(320), nullable=True)
    contact_phone = Column(String(80), nullable=True)
    whatsapp_display_phone = Column(String(80), nullable=True)
    whatsapp_business_account_id = Column(String(255), nullable=True)
    website_url = Column(String(2048), nullable=True)
    linkedin_url = Column(String(2048), nullable=True)
    facebook_url = Column(String(2048), nullable=True)
    instagram_url = Column(String(2048), nullable=True)
    whatsapp_url = Column(String(2048), nullable=True)
    logo_media_id = Column(Integer, ForeignKey("media.id", ondelete="SET NULL"), nullable=True, index=True)
    telegram_approval_chat_id = Column(String(255), nullable=True)
    telegram_approval_user_id = Column(String(255), nullable=True)
    telegram_approval_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    approval_required = Column(Boolean, nullable=False, default=True, server_default="true")
    approved_claims_json = Column(Text, nullable=True)
    prohibited_claims_json = Column(Text, nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="workspace_profile")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            name="workspace_profiles_organization_id_key",
        ),
    )


class WorkspaceSource(Base):
    """A user-supplied or officially connected source with provenance metadata."""

    __tablename__ = "workspace_sources"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=True)
    url = Column(String(2048), nullable=True)
    external_id = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    trust_level = Column(String(50), nullable=False, default="user_supplied")
    review_status = Column(String(50), nullable=False, default="pending")
    is_active = Column(Boolean, nullable=False, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="workspace_sources")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_type",
            "url",
            name="uq_workspace_source_org_type_url",
        ),
    )
