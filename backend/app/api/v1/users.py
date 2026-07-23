from fastapi import APIRouter, Depends, Query
from app.core.utils import get_client_ip
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List

from app.core.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.contact import Contact
from app.models.audit_log import AuditLog
from app.schemas.user import PaginatedUserResponse, UserAdminResponse, UserCreate, UserUpdate, UserStatusUpdate, LockedAccountResponse
from app.api.v1.auth import get_current_user
from fastapi import HTTPException, status, Request
import secrets
import datetime
from app.core.security import get_password_hash

def check_user_permissions(current_user: User, db: Session, target_role_id: Optional[int] = None, target_user: Optional[User] = None):
    if not current_user.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have a role assigned.")
        
    current_role = current_user.role.code
    
    if current_role == "ACCOUNT_MANAGER":
        if target_user and target_user.role and target_user.role.code != "COMPANY_CONTACT":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account Managers can only manage company contacts.")
        if target_role_id:
            target_role = db.query(Role).filter(Role.id == target_role_id).first()
            if not target_role or target_role.code != "COMPANY_CONTACT":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account Managers can only assign the Company Contact role.")
    elif current_role != "SYSTEM_ADMINISTRATOR":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only System Administrators and Account Managers have permission to manage users.")

router = APIRouter()

@router.get("/", response_model=PaginatedUserResponse)
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User).join(Role, User.role_id == Role.id).outerjoin(Contact, User.id == Contact.user_id)
    
    # Exclude contacts from the administrators list
    query = query.filter(Role.code != "COMPANY_CONTACT")

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        )
    
    if status and status.lower() != "all":
        query = query.filter(User.status == status.upper())
        
    if role and role.lower() != "all":
        query = query.filter(Role.name == role)

    # Get total count before pagination
    total_count = query.count()

    # Apply pagination and sorting
    users = query.order_by(User.created_at.desc(), User.id.desc()).offset(skip).limit(limit).all()

    items = []
    for u in users:
        # Resolve name
        name_str = f"{u.first_name or ''} {u.last_name or ''}".strip() or "Unnamed"
        items.append(UserAdminResponse(
            id=u.id,
            name=name_str,
            first_name=u.first_name,
            last_name=u.last_name,
            email=str(u.email),
            phone=u.phone_number,
            status=str(u.status),
            role_name=str(u.role.name) if u.role else "UNKNOWN",
            role_code=str(u.role.code) if u.role else None,
            last_login=u.last_login_at
        ))

    return PaginatedUserResponse(total_count=total_count, items=items)

@router.get("/locked/accounts", response_model=List[LockedAccountResponse])
def get_locked_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.core.redis import get_all_locked_accounts
    locked_redis = get_all_locked_accounts()
    
    if not locked_redis:
        return []
        
    user_ids = [item["user_id"] for item in locked_redis]
    query = db.query(User).filter(User.id.in_(user_ids))
    
    if current_user.role.code == "ACCOUNT_MANAGER":
        query = query.join(Role).filter(Role.code == "COMPANY_CONTACT")
        
    users = query.all()
    
    now = datetime.datetime.now()
    
    results = []
    for u in users:
        lock_info = next((item for item in locked_redis if item["user_id"] == u.id), None)
        if lock_info:
            ttl = lock_info["ttl"]
            duration = lock_info["duration"]
            unlocks_at = now + datetime.timedelta(seconds=ttl)
            locked_since = unlocks_at - datetime.timedelta(seconds=duration)
            
            results.append(LockedAccountResponse(
                id=u.id,
                first_name=u.first_name or "",
                last_name=u.last_name or "",
                email=str(u.email),
                locked_since=locked_since,
                unlocks_at=unlocks_at
            ))
            
    return results

@router.post("/{user_id}/unlock")
def unlock_user(user_id: int, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    check_user_permissions(current_user, db, target_user=target_user)
        
    from app.core.redis import clear_account_lock
    clear_account_lock(user_id)
    
    # Also unlock manually in DB if it was set
    if target_user.status == 'LOCKED':
        target_user.status = 'ACTIVE'
        
    from app.api.v1.system_settings import get_setting
    bypass_hours = int(get_setting(db, "password_only_duration"))
    # Grant bypass_hours of OTP bypass
    target_user.password_only_until = datetime.datetime.now() + datetime.timedelta(hours=bypass_hours)
    
    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Account Unlocked',
        entity_type='User',
        entity_id=target_user.id,
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()
        
    return {"message": "Account unlocked successfully."}

@router.post('/', response_model=UserAdminResponse)
def create_user(payload: UserCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if user already exists
    if db.query(User).filter(User.email == payload.email.strip().lower()).first():
        raise HTTPException(status_code=400, detail='Email already registered')

    # RBAC Security Check
    check_user_permissions(current_user, db, target_role_id=payload.role_id)

    # Verify role exists
    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail='Role not found')

    # Generate random password
    random_password = secrets.token_urlsafe(16)
    password_hash = get_password_hash(random_password)

    new_user = User(
        email=payload.email.strip().lower(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=password_hash,
        role_id=role.id,
        status='ACTIVE',
        first_login=True
    )
    if payload.phone:
        new_user.phone_number = payload.phone

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Administrator Created',
        entity_type='User',
        entity_id=new_user.id,
        new_values={'email': new_user.email, 'role': role.name},
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()

    # Trigger password reset email for the new user
    from app.core.redis import set_reset_token
    from app.core.config import settings
    from app.tasks.email_tasks import send_password_reset_email
    
    reset_token = secrets.token_urlsafe(32)
    set_reset_token(reset_token, new_user.id)
    
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Send the password reset email synchronously (fast enough for admin-only user creation)
    send_password_reset_email(new_user.email, reset_link, "fr")

    return UserAdminResponse(
        id=new_user.id,
        name=f"{new_user.first_name} {new_user.last_name}",
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=str(new_user.email),
        phone=new_user.phone_number,
        status=str(new_user.status),
        role_name=str(role.name),
        last_login=new_user.last_login_at
    )

@router.put('/{user_id}', response_model=UserAdminResponse)
def update_user(user_id: int, payload: UserUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail='User not found')

    # RBAC Security Check
    check_user_permissions(current_user, db, target_role_id=payload.role_id, target_user=target_user)

    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail='Role not found')

    target_user.role_id = role.id
    target_user.first_name = payload.first_name
    target_user.last_name = payload.last_name
    if payload.phone:
        target_user.phone_number = payload.phone

    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Administrator Updated',
        entity_type='User',
        entity_id=target_user.id,
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()

    name = f"{target_user.first_name} {target_user.last_name}" if target_user.first_name and target_user.last_name else str(target_user.email).split('@')[0]
    return UserAdminResponse(
        id=target_user.id,
        name=name,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        email=str(target_user.email),
        phone=target_user.phone_number,
        status=str(target_user.status),
        role_name=str(role.name),
        last_login=target_user.last_login_at
    )

@router.patch('/{user_id}/status')
def update_user_status(user_id: int, payload: UserStatusUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail='User not found')

    # RBAC Security Check
    check_user_permissions(current_user, db, target_user=target_user)

    old_status = target_user.status
    target_user.status = payload.status.upper()

    action_str = 'Administrator Enabled' if target_user.status == 'ACTIVE' else 'Administrator Disabled'
    audit_entry = AuditLog(
        user_id=current_user.id,
        action=action_str,
        entity_type='User',
        entity_id=target_user.id,
        old_values={'status': str(old_status)},
        new_values={'status': str(target_user.status)},
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()

    return {'message': f'Status updated to {target_user.status}'}

@router.get('/roles')
def get_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    roles = db.query(Role).all()
    return [{"id": r.id, "code": r.code, "name": r.name, "description": r.description} for r in roles]
