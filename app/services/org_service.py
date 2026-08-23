"""Service for managing Organizations and memberships."""
from typing import List, Optional
from sqlalchemy.orm import Session
import json

from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.workspace_intelligence import WorkspaceProfile
from app.services.audit_service import AuditService


def _is_hinglish_quote_workspace(name: str, slug: str) -> bool:
    signal = f"{name} {slug}".casefold()
    return any(term in signal for term in ("love", "truth", "motivational", "pain", "quotes", "quote"))


class OrgService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService()

    def create_organization(self, name: str, slug: str, creator_id: int) -> Organization:
        """Create a new organization and add the creator as OWNER."""
        org = Organization(name=name, slug=slug, created_by_id=creator_id)
        self.db.add(org)
        self.db.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=creator_id,
            role=OrganizationRole.OWNER
        )
        self.db.add(member)

        if _is_hinglish_quote_workspace(name, slug):
            self.db.add(WorkspaceProfile(
                organization_id=org.id,
                business_description=(
                    "A social media quote page sharing Love, Truth, Motivational, and Pain quotes "
                    "in natural Hinglish using Roman Hindi and English."
                ),
                mission="Make relatable emotions and life lessons easy to feel and share.",
                tagline="Dil ki baat, Hinglish alfaaz mein.",
                industry="Hinglish quotes and digital content",
                services_json=json.dumps(["Hinglish quote content", "Branded social media image posts"]),
                products_json=json.dumps(["Love quotes", "Truth quotes", "Motivational quotes", "Pain quotes"]),
                target_audience="People who connect with relatable love, reality, motivation, healing, and pain content.",
                brand_voice="Emotional, relatable, concise, poetic, honest, and never preachy.",
                tone="Warm, heartfelt, reflective, hopeful, and authentic.",
                visual_style="Image-led quote cards with strong text-safe areas, expressive photography or gradients, bold hierarchy, and a consistent branded footer.",
                brand_colors_json=json.dumps(["#111827", "#F59E0B", "#F8FAFC", "#EC4899"]),
                font_preferences_json=json.dumps(["DejaVu Sans", "DejaVu Serif"]),
                preferred_content_formats_json=json.dumps(["branded quote image", "square social card", "carousel quote story"]),
                keywords_json=json.dumps(["love", "truth", "motivation", "pain", "healing", "dard", "pyaar", "sach", "zindagi"]),
                preferred_languages_json=json.dumps(["Hinglish", "Roman Hindi", "English"]),
                approval_required=True,
            ))
        
        self.audit.log_action(
            db=self.db,
            action="org.created",
            entity_type="organization",
            entity_id=org.id,
            user_id=creator_id,
            description=f"Organization '{name}' created"
        )
        
        self.db.commit()
        self.db.refresh(org)
        return org

    def get_org(self, org_id: int) -> Optional[Organization]:
        """Fetch an organization by ID."""
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def verify_admin_access(self, org_id: int, user_id: int) -> bool:
        """Verify if a user has ADMIN or OWNER role in an organization."""
        member = (
            self.db.query(OrganizationMember)
            .filter(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == user_id)
            .first()
        )
        return member is not None and member.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]

    def get_user_organizations(self, user_id: int) -> List[Organization]:
        """List all organizations where the user is a member."""
        return (
            self.db.query(Organization)
            .join(OrganizationMember)
            .filter(OrganizationMember.user_id == user_id)
            .all()
        )

    def get_organization_members(self, org_id: int) -> List[OrganizationMember]:
        """List all members of an organization."""
        return (
            self.db.query(OrganizationMember)
            .filter(OrganizationMember.organization_id == org_id)
            .all()
        )

    def add_member(self, org_id: int, user_id: int, role: OrganizationRole, admin_id: int) -> OrganizationMember:
        """Add a user to an organization."""
        # Verification of admin_id's role should happen in API layer or here
        member = OrganizationMember(organization_id=org_id, user_id=user_id, role=role)
        self.db.add(member)
        
        self.audit.log_action(
            db=self.db,
            action="org.member_added",
            entity_type="organization",
            entity_id=org_id,
            user_id=admin_id,
            description=f"User {user_id} added to org {org_id} as {role.value}"
        )
        
        self.db.commit()
        return member

    def remove_member(self, org_id: int, user_id: int, admin_id: int) -> bool:
        """Remove a member from an organization."""
        member = (
            self.db.query(OrganizationMember)
            .filter(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == user_id)
            .first()
        )
        if not member:
            return False
            
        if member.role == OrganizationRole.OWNER:
            raise ValueError("Cannot remove the OWNER of an organization")
            
        self.db.delete(member)
        
        self.audit.log_action(
            db=self.db,
            action="org.member_removed",
            entity_type="organization",
            entity_id=org_id,
            user_id=admin_id,
            description=f"User {user_id} removed from org {org_id}"
        )
        
        self.db.commit()
        return True
