from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SystemSettingsUpdate, SystemSettingsResponse
from app.api.v1.auth import get_current_user

router = APIRouter()

DEFAULT_SETTINGS = {
    "code_expiration": "5",
    "max_signin_attempts": "3",
    "lock_duration": "24",
    "password_only_duration": "1",
    "default_language": "French",
    "email_provider": "Brevo"
}

def get_setting(db: Session, key: str) -> str:
    setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
    if setting:
        return setting.setting_value
    return DEFAULT_SETTINGS.get(key, "")

@router.get("/", response_model=SystemSettingsResponse)
def get_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings_dict = {}
    for key, default_val in DEFAULT_SETTINGS.items():
        val = get_setting(db, key)
        settings_dict[key] = val
        
    return SystemSettingsResponse(
        code_expiration=int(settings_dict.get("code_expiration", 5)),
        max_signin_attempts=int(settings_dict.get("max_signin_attempts", 3)),
        lock_duration=int(settings_dict.get("lock_duration", 24)),
        password_only_duration=int(settings_dict.get("password_only_duration", 1)),
        default_language=settings_dict.get("default_language", "French"),
        email_provider=settings_dict.get("email_provider", "Brevo")
    )

@router.put("/", response_model=SystemSettingsResponse)
def update_settings(payload: SystemSettingsUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # RBAC: only privileged roles may change system-wide security settings
    role_code: str = current_user.role.code if current_user.role else "UNKNOWN"  # type: ignore[assignment]
    if role_code not in ("SYSTEM_ADMINISTRATOR", "ACCOUNT_MANAGER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs système ou gestionnaires de compte peuvent modifier les paramètres système."
        )

    update_data = payload.model_dump()
    # email_provider is not editable through the settings form
    update_data["email_provider"] = get_setting(db, "email_provider") or "Brevo"

    for key, val in update_data.items():
        setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
        if setting:
            setting.setting_value = str(val)
        else:
            new_setting = SystemSetting(setting_key=key, setting_value=str(val))
            db.add(new_setting)

    db.commit()
    
    # Notify other System Admins
    from app.core.notification_service import notify_system_admins
    from app.core.utils import user_display_name
    admin_name = user_display_name(current_user)
    notify_system_admins(
        db,
        "System Settings Updated",
        f"The system settings were modified by {current_user.first_name} {current_user.last_name}.",
        type="INFO",
        exclude_user_id=current_user.id,
        action_url="/admin/settings"
    )
    return get_settings(db=db, current_user=current_user)
