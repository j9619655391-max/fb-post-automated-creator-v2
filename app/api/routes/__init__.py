from fastapi import APIRouter, Depends
from app.api.dependencies import check_maintenance_mode
from app.api.routes import content, users, audit_logs, auth_facebook, meta_pages, scheduled_posts, cron, vce, auth, media, ai, instagram, auth_linkedin, platforms, organizations, billing, admin_settings, generation, generation_plans, workspace_intelligence

api_router = APIRouter(dependencies=[Depends(check_maintenance_mode)])

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(auth_facebook.router, prefix="/auth/facebook", tags=["auth"])
api_router.include_router(auth_linkedin.router, prefix="/auth/linkedin", tags=["auth"])
api_router.include_router(meta_pages.router, prefix="/meta/pages", tags=["meta-pages"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(workspace_intelligence.router, prefix="/organizations", tags=["workspace-intelligence"])

api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(admin_settings.router, prefix="/admin/settings", tags=["admin-settings"])
api_router.include_router(scheduled_posts.router, prefix="/scheduled-posts", tags=["scheduled-posts"])

api_router.include_router(cron.router, prefix="/cron", tags=["cron"])
api_router.include_router(vce.router, prefix="/vce", tags=["vce"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(generation_plans.router, prefix="/generation-plans", tags=["generation-plans"])
api_router.include_router(instagram.router, prefix="/instagram", tags=["instagram"])




