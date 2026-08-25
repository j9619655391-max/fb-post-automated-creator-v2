"""Media model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Media(Base):
    """Model for uploaded media files (images/videos)."""
    
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_size = Column(Integer, nullable=False)
    source_kind = Column(String(40), nullable=False, default="uploaded")
    source_url = Column(String(2048), nullable=True)
    license_info = Column(Text, nullable=True)
    attribution = Column(Text, nullable=True)
    provenance_status = Column(String(30), nullable=False, default="unverified")

    # Ownership
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    organization = relationship("Organization", backref="media_assets")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    owner = relationship("User", backref="media")

    def __repr__(self):
        return f"<Media(id={self.id}, filename='{self.filename}', mime_type='{self.mime_type}')>"
