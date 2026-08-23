from app.models.organization import Organization
from app.models.user import User
from app.models.workspace_intelligence import WorkspaceProfile
from scripts.init_db import _seed_categories as seed_categories_for_test
from app.services.vce_service import get_recommended_category, list_categories


def _workspace(db, *, name: str, industry: str, description: str):
    user = User(
        username=f"{name.lower().replace(' ', '-')}-owner",
        email=f"{name.lower().replace(' ', '-')}@example.com",
        full_name="Workspace Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(name=name, slug=name.lower().replace(' ', '-'), created_by_id=user.id)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    profile = WorkspaceProfile(
        organization_id=organization.id,
        industry=industry,
        business_description=description,
    )
    db.add(profile)
    db.commit()
    return organization


def test_category_recommendation_uses_workspace_business_signal(db):
    seed_categories_for_test(db)
    db.commit()
    aaditech = _workspace(
        db,
        name="Aaditech Solution",
        industry="Digital marketing and technology services",
        description="We help businesses with digital marketing, websites, software and technology solutions.",
    )
    kashvera = _workspace(
        db,
        name="Kashvera Fashion Designer",
        industry="Fashion design and tailoring",
        description="A fashion designer creating tailored suits, occasion wear and styling experiences.",
    )

    aaditech_category, _, _ = get_recommended_category(db, aaditech.id)
    kashvera_category, _, _ = get_recommended_category(db, kashvera.id)

    assert aaditech_category is not None
    assert kashvera_category is not None
    assert aaditech_category.slug in {"service-showcase", "case-study-results", "educational-howto", "industry-insights"}
    assert kashvera_category.slug in {"product-showcase", "collection-launch", "bridal-occasion", "styling-tips", "fabric-craft"}
    assert aaditech_category.slug not in {"motivation", "reflection"}
    assert kashvera_category.slug not in {"motivation", "reflection"}


def test_workspace_ranked_category_list_places_business_fit_first(db):
    seed_categories_for_test(db)
    db.commit()
    workspace = _workspace(db, name="Aaditech Solution", industry="Digital marketing agency", description="Marketing solutions for businesses")
    categories = list_categories(db, workspace.id)
    assert categories
    assert categories[0].slug in {"service-showcase", "case-study-results", "educational-howto", "industry-insights", "offer-booking"}
