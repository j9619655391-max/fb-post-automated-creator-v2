from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.billing_service import BillingService
from app.services.org_service import OrgService
from pydantic import BaseModel

router = APIRouter()

class CheckoutRequest(BaseModel):
    organization_id: int
    price_id: str
    success_url: str
    cancel_url: str

class PortalRequest(BaseModel):
    organization_id: int
    return_url: str


@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a subscription checkout for an organization."""
    org_service = OrgService(db)
    org = org_service.get_org(req.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Permission check: Only OWNER or ADMIN can manage billing
    if not org_service.verify_admin_access(org.id, current_user.id):
        raise HTTPException(status_code=403, detail="Only owners and admins can manage billing")

    billing_service = BillingService(db)
    try:
        url = billing_service.create_checkout_session(
            org, 
            req.price_id, 
            req.success_url, 
            req.cancel_url
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
async def create_portal(
    req: PortalRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate a link to the Stripe Customer Portal."""
    org_service = OrgService(db)
    org = org_service.get_org(req.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org_service.verify_admin_access(org.id, current_user.id):
        raise HTTPException(status_code=403, detail="Only owners and admins can manage billing")

    billing_service = BillingService(db)
    try:
        url = billing_service.create_portal_session(org, req.return_url)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage")
async def get_generation_usage(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return AI generation token/cost usage for an organization admin."""
    org_service = OrgService(db)
    org = org_service.get_org(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not org_service.verify_admin_access(org.id, current_user.id):
        raise HTTPException(status_code=403, detail="Only owners and admins can view billing usage")
    return BillingService(db).get_generation_usage(org)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Stripe webhook listener to sync subscription status."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
    payload = await request.body()
    billing_service = BillingService(db)
    try:
        billing_service.handle_webhook(payload, stripe_signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In production, log this error
        raise HTTPException(status_code=500, detail="Webhook handling failed")
