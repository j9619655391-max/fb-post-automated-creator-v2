from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WorkspaceClaim(Base):
    __tablename__ = "workspace_claims"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), nullable=False, default="approved_fact")
    review_status = Column(String(30), nullable=False, default="pending")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    evidence_links = relationship("WorkspaceClaimSource", back_populates="claim", cascade="all, delete-orphan")


class WorkspaceClaimSource(Base):
    __tablename__ = "workspace_claim_sources"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("workspace_claims.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("workspace_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    claim = relationship("WorkspaceClaim", back_populates="evidence_links")
    source = relationship("WorkspaceSource")

    __table_args__ = (
        UniqueConstraint("claim_id", "source_id", name="uq_workspace_claim_source"),
    )


class ContentPackageEvidence(Base):
    __tablename__ = "content_package_evidence"

    id = Column(Integer, primary_key=True, index=True)
    content_package_id = Column(Integer, ForeignKey("content_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("workspace_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    claim_id = Column(Integer, ForeignKey("workspace_claims.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_type = Column(String(40), nullable=False, default="grounding")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    package = relationship("ContentPackage")
    source = relationship("WorkspaceSource")
    claim = relationship("WorkspaceClaim")
