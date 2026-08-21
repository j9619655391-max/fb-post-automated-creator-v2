"""LinkedIn Account model (User Profiles or Company Pages)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class LinkedInAccount(Base):
    """LinkedIn Profile or Company Page linked to a user."""
    __tablename__ = "linkedin_accounts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    linkedin_id = Column(String(64), nullable=False, index=True) # e.g. 'urn:li:person:...' or 'urn:li:organization:...'
    name = Column(String(255), nullable=True)
    account_type = Column(String(32), default="person") # "person" or "organization"
    organization_role = Column(String(64), nullable=True)
    organization_role_state = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "linkedin_id", name="uq_linkedin_accounts_user_id"),)

    user = relationship("User", backref="linkedin_accounts")
