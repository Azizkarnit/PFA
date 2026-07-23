from fastapi import APIRouter
from app.api.v1 import auth, dashboard, users, companies, contacts, audit_logs, system_settings, surveys, portal, notifications, external_integration

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(system_settings.router, prefix="/system-settings", tags=["system-settings"])
api_router.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
api_router.include_router(portal.router, prefix="/portal", tags=["portal"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(external_integration.router, prefix="/ext", tags=["external-integration"])
