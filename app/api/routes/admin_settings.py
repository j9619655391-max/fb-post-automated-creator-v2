from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.settings_service import SettingsService
from app.services.audit_service import AuditService
from pydantic import BaseModel, ConfigDict
from typing import Optional

router = APIRouter()

class SettingUpdate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    description: str = None

class SettingResponse(BaseModel):
    key: str
    value: str
    is_encrypted: bool
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


def verify_super_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can access system settings"
        )
    return current_user

@router.post("/update")
def update_setting(
    req: SettingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    service = SettingsService(db)
    setting = service.update_setting(
        req.key, 
        req.value, 
        encrypt=req.is_encrypted, 
        description=req.description
    )
    return {"status": "success", "key": setting.key}

@router.get("/test/stripe")
def test_stripe(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    service = SettingsService(db)
    return service.test_stripe_connectivity()

@router.get("/test/gdrive")
def test_gdrive(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    service = SettingsService(db)
    return service.test_google_drive_connectivity()

@router.get("/keys")
def list_keys(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """List all configured keys (values obscured if encrypted)."""
    from app.models.system_setting import SystemSetting
    settings = db.query(SystemSetting).all()
    
    results = []
    for s in settings:
        val = s.value
        if s.is_encrypted and val:
            val = "********" # Obscure encrypted keys in the list
        results.append({
            "key": s.key,
            "value": val,
            "is_encrypted": s.is_encrypted,
            "description": s.description,
            "updated_at": s.updated_at
        })
    return results

@router.post("/sync-env")
def sync_env(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """Sync database settings to the .env file."""
    service = SettingsService(db)
    try:
        service.sync_to_env()
        return {"status": "success", "message": "Settings synchronized to .env file"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

# --- USER MANAGEMENT ---

@router.get("/users")
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """Global list of all users."""
    users = db.query(User).all()
    return users

@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """Ban or reactivate a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    return {"status": "success", "user_id": user_id, "is_active": is_active}

# --- ORGANIZATION OVERSIGHT ---

@router.get("/organizations")
def list_all_orgs(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """Global list of all organizations with their subscription status."""
    from app.models.organization import Organization
    orgs = db.query(Organization).all()
    return orgs

@router.post("/organizations/{org_id}/tier")
def update_org_tier(
    org_id: int,
    tier: str,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """Manually override an organization's subscription tier."""
    from app.models.organization import Organization, SubscriptionTier
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        org.subscription_tier = SubscriptionTier(tier.lower())
        org.subscription_status = "active" # Manual override is usually active
        db.commit()
        return {"status": "success", "tier": tier}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

# --- AUDIT LOGS ---

@router.get("/audit-logs")
def get_global_audit_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_super_admin)
):
    """View global action trail."""
    from app.models.audit_log import AuditLog
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
    return logs
