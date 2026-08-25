from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PamphletBrief(Base):
    __tablename__ = "pamphlet_briefs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    objective = Column(String(120), nullable=True)
    audience = Column(String(500), nullable=True)
    panel_count = Column(Integer, nullable=False, default=2)
    paper_size = Column(String(40), nullable=False, default="A4")
    orientation = Column(String(20), nullable=False, default="landscape")
    fold_style = Column(String(40), nullable=False, default="half-fold")
    trim_width_mm = Column(Integer, nullable=False, default=297)
    trim_height_mm = Column(Integer, nullable=False, default=210)
    bleed_mm = Column(Integer, nullable=False, default=3)
    safe_area_mm = Column(Integer, nullable=False, default=5)
    qr_url = Column(String(2048), nullable=True)
    accessibility_text = Column(Text, nullable=True)
    content_json = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="draft")
    approval_required = Column(Boolean, nullable=False, default=True, server_default="true")
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    created_by = relationship("User")
