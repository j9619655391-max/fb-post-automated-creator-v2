"""Facebook OAuth routes with authenticated, server-side initiation state."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.facebook_oauth_service import disconnect_facebook, exchange_code, get_authorize_url

router = APIRouter()


@router.post("/login")
def facebook_login(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a short-lived server-side OAuth state and return the provider URL."""
    try:
        return {"authorize_url": get_authorize_url(db, current_user.id)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/callback")
def facebook_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """Exchange a single-use, expiring provider state for an encrypted token."""
    try:
        exchange_code(db, code, state)
    except ValueError:
        return RedirectResponse(url="/?error=facebook_callback", status_code=302)
    return RedirectResponse(url="/?facebook=connected", status_code=302)


@router.post("/disconnect")
def facebook_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    disconnected = disconnect_facebook(db, current_user.id)
    if not disconnected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facebook was not connected")
    return {"disconnected": True}
