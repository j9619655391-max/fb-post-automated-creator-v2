from app.models.linkedin_account import LinkedInAccount
from app.models.linkedin_oauth import LinkedInUserToken
from app.models.meta_oauth import MetaUserToken
from app.models.meta_page import MetaPage
from app.models.content import Content, ContentStatus


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = ""
        self.headers = {}

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = responses

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, **kwargs):
        return self.responses[url]


def test_meta_sync_persists_instagram_professional_account(db, monkeypatch):
    from app.services import facebook_pages_service

    db.add(MetaUserToken(user_id=1, access_token_encrypted="cipher"))
    db.commit()
    response = FakeResponse({
        "data": [{
            "id": "page-1",
            "name": "Business Page",
            "access_token": "page-token",
            "category": "Business",
            "instagram_business_account": {"id": "ig-1"},
        }]
    })
    monkeypatch.setattr(facebook_pages_service, "decrypt_token", lambda value: "user-token")
    monkeypatch.setattr(facebook_pages_service, "encrypt_token", lambda value: f"encrypted:{value}")
    monkeypatch.setattr(
        facebook_pages_service.httpx,
        "Client",
        lambda: FakeClient({"https://graph.facebook.com/v18.0/me/accounts": response}),
    )

    assert facebook_pages_service.sync_pages(db, 1) == 1
    page = db.query(MetaPage).filter(MetaPage.page_id == "page-1").one()
    assert page.instagram_business_account_id == "ig-1"


def test_linkedin_sync_discovers_approved_organization(db, monkeypatch):
    from app.services import linkedin_api

    db.add(LinkedInUserToken(user_id=1, access_token_encrypted="cipher"))
    db.commit()
    responses = {
        "https://api.linkedin.com/v2/userinfo": FakeResponse({"sub": "member-1", "name": "Member One"}),
        "https://api.linkedin.com/rest/organizationAcls": FakeResponse({
            "elements": [{
                "organization": "urn:li:organization:123",
                "role": "ADMINISTRATOR",
                "state": "APPROVED",
            }]
        }),
    }
    monkeypatch.setattr(linkedin_api, "decrypt_token", lambda value: "linkedin-token")
    monkeypatch.setattr(linkedin_api.httpx, "Client", lambda: FakeClient(responses))

    assert linkedin_api.sync_linkedin_accounts(db, 1) == 2
    organization = db.query(LinkedInAccount).filter(LinkedInAccount.account_type == "organization").one()
    assert organization.linkedin_id == "urn:li:organization:123"
    assert organization.organization_role == "ADMINISTRATOR"
    assert organization.organization_role_state == "APPROVED"


def test_instagram_polls_container_until_finished(db, monkeypatch):
    from app.core.config import settings
    from app.core import token_crypto
    from app.services import fb_api
    import httpx

    content = Content(title="Launch", body="A public announcement", status=ContentStatus.APPROVED, created_by_id=1)
    page = MetaPage(
        user_id=1,
        page_id="page-1",
        page_name="Business Page",
        access_token_encrypted="cipher",
        instagram_business_account_id="ig-1",
    )
    db.add_all([content, page])
    db.commit()

    class InstagramClient(FakeClient):
        def __init__(self):
            self.statuses = iter([
                FakeResponse({"status_code": "IN_PROGRESS", "status": "Processing"}),
                FakeResponse({"status_code": "FINISHED", "status": "Ready"}),
            ])
            self.published = False

        def get(self, url, **kwargs):
            if url.endswith("/content_publishing_limit"):
                return FakeResponse({"data": [{"quota_usage": 1, "config": {"quota_total": 50}}]})
            if url.endswith("/container-1"):
                return next(self.statuses)
            raise AssertionError(f"Unexpected GET: {url}")

        def post(self, url, **kwargs):
            if url.endswith("/media"):
                return FakeResponse({"id": "container-1"})
            if url.endswith("/media_publish"):
                self.published = True
                return FakeResponse({"id": "ig-media-1"})
            raise AssertionError(f"Unexpected POST: {url}")

    client = InstagramClient()
    monkeypatch.setattr(token_crypto, "decrypt_token", lambda value: "page-token")
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)
    monkeypatch.setattr(settings, "instagram_container_poll_attempts", 5)
    monkeypatch.setattr(settings, "instagram_container_poll_interval_seconds", 0)

    result = fb_api.publish_to_instagram(db, content.id, page.id, 1, "https://cdn.example.com/image.jpg")

    assert result == {"ig_media_id": "ig-media-1"}
    assert client.published is True
