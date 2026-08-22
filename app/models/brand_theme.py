from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BrandTheme(Base):
    """Reusable workspace-owned visual and editorial theme definition."""

    __tablename__ = "brand_themes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    visual_style = Column(Text, nullable=True)
    color_palette_json = Column(Text, nullable=True)
    typography_json = Column(Text, nullable=True)
    logo_position = Column(String(50), nullable=False, default="bottom_right")
    background_style = Column(String(100), nullable=True)
    supported_formats_json = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_default = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", backref="brand_themes")

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_brand_themes_org_slug"),
    )
