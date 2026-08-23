"""LinkedIn OAuth routes with authenticated, server-side initiation state."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.linkedin_oauth_service import disconnect_linkedin, exchange_code, get_authorize_url

router = APIRouter()


@router.post("/login")
def linkedin_login(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a short-lived server-side OAuth state and return the provider URL."""
    try:
        return {"authorize_url": get_authorize_url(db, current_user.id)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/login", include_in_schema=False)
def deprecated_linkedin_login_get():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use POST /auth/linkedin/login")


@router.get("/callback")
def linkedin_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    try:
        exchange_code(db, code, state)
    except ValueError:
        return RedirectResponse(url="/?error=linkedin_callback", status_code=302)
    return RedirectResponse(url="/?linkedin=connected", status_code=302)


@router.post("/disconnect")
def linkedin_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    disconnected = disconnect_linkedin(db, current_user.id)
    if not disconnected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn was not connected")
    return {"disconnected": True}
