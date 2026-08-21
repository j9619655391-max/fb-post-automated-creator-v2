"""LinkedIn API integration: publish content to LinkedIn."""
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.token_crypto import decrypt_token

from app.models.content import Content
from app.models.linkedin_account import LinkedInAccount
from app.models.content_execution import ContentPublishStatus, PublishStatusEnum
from app.services.publish_errors import classify_publish_failure


def _linkedin_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": settings.linkedin_api_version,
        "X-Restli-Protocol-Version": "2.0.0",
    }


def sync_linkedin_accounts(db: Session, user_id: int) -> int:

    """
    Fetch LinkedIn profile (and potentially pages) and upsert into linkedin_accounts.
    Returns count of accounts synced.
    """
    from app.models.linkedin_oauth import LinkedInUserToken
    user_token_row = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).first()
    if not user_token_row:
        raise ValueError("LinkedIn not connected")
    
    access_token = decrypt_token(user_token_row.access_token_encrypted)
    
    try:
        with httpx.Client() as client:
            # Get User Info (OpenID Connect)
            resp = client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if not resp.is_success:
                raise ValueError(f"LinkedIn sync failed: {resp.text}")
            
            user_info = resp.json()
            linkedin_id = f"urn:li:person:{user_info['sub']}"
            name = user_info.get("name", "LinkedIn User")
            
            # Upsert
            existing = db.query(LinkedInAccount).filter(
                LinkedInAccount.user_id == user_id,
                LinkedInAccount.linkedin_id == linkedin_id
            ).first()
            
            if existing:
                existing.name = name
            else:
                db.add(LinkedInAccount(
                    user_id=user_id,
                    linkedin_id=linkedin_id,
                    name=name,
                    account_type="person"
                ))
            
            # Discover approved organization roles without publishing. This endpoint
            # may be unavailable until LinkedIn grants the organization permissions;
            # retain the member account when that happens.
            try:
                acl_resp = client.get(
                    "https://api.linkedin.com/rest/organizationAcls",
                    headers=_linkedin_headers(access_token),
                    params={
                        "q": "roleAssignee",
                        "role": "ADMINISTRATOR",
                        "state": "APPROVED",
                    },
                )
                acl_elements = acl_resp.json().get("elements", []) if acl_resp.is_success else []
            except (httpx.HTTPError, ValueError):
                acl_elements = []

            synced = 1
            for element in acl_elements:
                organization_urn = element.get("organization") or element.get("organizationTarget")
                if not organization_urn:
                    continue
                existing_org = db.query(LinkedInAccount).filter(
                    LinkedInAccount.user_id == user_id,
                    LinkedInAccount.linkedin_id == organization_urn,
                ).first()
                if existing_org:
                    existing_org.name = organization_urn
                    existing_org.account_type = "organization"
                    existing_org.organization_role = element.get("role")
                    existing_org.organization_role_state = element.get("state")
                else:
                    db.add(LinkedInAccount(
                        user_id=user_id,
                        linkedin_id=organization_urn,
                        name=organization_urn,
                        account_type="organization",
                        organization_role=element.get("role"),
                        organization_role_state=element.get("state"),
                    ))
                synced += 1

            db.commit()
            return synced

    except Exception as e:
        raise ValueError(f"LinkedIn sync error: {str(e)}")


def publish_to_linkedin(
    db: Session,
    content_id: int,
    linkedin_account_ids: list[int],
    user_id: int,
) -> Content:
    """
    Publish content to multiple LinkedIn Accounts (Profiles or Pages).
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise ValueError("Content not found")

    if content.status != "approved":
        raise ValueError("Content must be APPROVED to publish to LinkedIn")

    from app.models.linkedin_oauth import LinkedInUserToken
    user_token_row = db.query(LinkedInUserToken).filter(LinkedInUserToken.user_id == user_id).first()
    if not user_token_row:
        raise ValueError("LinkedIn not connected for this user.")
    
    access_token = decrypt_token(user_token_row.access_token_encrypted)
    content_text = f"{content.title}\n\n{content.body}"

    for account_id in linkedin_account_ids:
        account = db.query(LinkedInAccount).filter(LinkedInAccount.id == account_id, LinkedInAccount.user_id == user_id).first()
        if not account:
            continue

        publish_status = ContentPublishStatus(
            content_id=content.id,
            linkedin_account_id=account.id,
            status=PublishStatusEnum.PROCESSING
        )
        db.add(publish_status)
        db.commit()

        if account.account_type == "organization" and not (
            account.organization_role_state == "APPROVED"
            and account.organization_role in {"ADMINISTRATOR", "DIRECT_SPONSORED_CONTENT_POSTER", "CONTENT_ADMINISTRATOR"}
        ):
            publish_status.status = PublishStatusEnum.FAILED
            publish_status.error_message = "PERMISSION_REQUIRED: LinkedIn organization role is not approved for publishing."
            db.commit()
            continue

        try:

            # LinkedIn Posts API (modern)
            # POST https://api.linkedin.com/rest/posts
            # Note: Requires 'LinkedIn-Version' header. 
            # Version '202312' is common.
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": settings.linkedin_api_version,

                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            
            post_data = {
                "author": account.linkedin_id,
                "commentary": content_text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            
            # If media exists, we'd handle it here (requires upload flow)
            # For now, text-only MVP
            
            with httpx.Client() as client:
                resp = client.post("https://api.linkedin.com/rest/posts", headers=headers, json=post_data)
                if not resp.is_success:
                    error_data = resp.text
                    raise ValueError(f"LinkedIn API error: {error_data}")
                
                # LinkedIn returns the URN of the created post in the 'x-linkedin-id' header
                platform_post_id = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")

            publish_status.platform_post_id = platform_post_id
            publish_status.status = PublishStatusEnum.POSTED
        except Exception as e:
            classification = classify_publish_failure(e)
            publish_status.status = PublishStatusEnum.FAILED
            publish_status.error_message = f"{classification.code}: {classification.message}"
            
        db.commit()

    db.refresh(content)
    return content
