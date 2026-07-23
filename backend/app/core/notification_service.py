import json
from sqlalchemy.orm import Session
from app.models.app_notification import AppNotification
from app.models.user import User
from app.models.role import Role
from app.core.redis import get_redis_client

def create_notification(db: Session, user_id: int, title: str, message: str, type: str = "INFO", action_url: str = None):
    """
    Creates a notification in the database and publishes it to Redis for real-time delivery.
    """
    notif = AppNotification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        action_url=action_url,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    # Publish to Redis
    payload = {
        "id": notif.id,
        "user_id": notif.user_id,
        "title": notif.title,
        "message": notif.message,
        "type": notif.type,
        "action_url": notif.action_url,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat()
    }
    redis_client = get_redis_client()
    redis_client.publish("notifications_channel", json.dumps(payload))
    return notif

def notify_system_admins(db: Session, title: str, message: str, type: str = "INFO", exclude_user_id: int = None, action_url: str = None):
    """Notify all SYSTEM_ADMINISTRATORs."""
    admins = db.query(User).join(Role).filter(Role.code == "SYSTEM_ADMINISTRATOR").all()
    for admin in admins:
        if exclude_user_id and admin.id == exclude_user_id:
            continue
        create_notification(db, admin.id, title, message, type, action_url)

def notify_account_managers(db: Session, title: str, message: str, type: str = "INFO", action_url: str = None):
    """Notify all ACCOUNT_MANAGERs."""
    managers = db.query(User).join(Role).filter(Role.code == "ACCOUNT_MANAGER").all()
    for manager in managers:
        create_notification(db, manager.id, title, message, type, action_url)

def notify_survey_admins_for_survey(db: Session, survey_id: int, title: str, message: str, type: str = "INFO", action_url: str = None):
    """Notify SURVEY_ADMINISTRATORs assigned to a specific survey, excluding ACCOUNT_MANAGERs."""
    from app.models.survey_assignment import SurveyAssignment
    
    assigned_users = (
        db.query(User)
        .join(SurveyAssignment, SurveyAssignment.user_id == User.id)
        .join(Role, Role.id == User.role_id)
        .filter(
            SurveyAssignment.survey_id == survey_id,
            Role.code != "ACCOUNT_MANAGER"
        )
        .all()
    )
    
    for user in assigned_users:
        create_notification(db, user.id, title, message, type, action_url)
