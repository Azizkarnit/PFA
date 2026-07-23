import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from app.core.utils import get_client_ip
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, asc, desc
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.contact import Contact
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.api.v1.auth import get_current_user
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse, PaginatedContactResponse

router = APIRouter()

@router.get("", response_model=PaginatedContactResponse)
def get_contacts(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Contact, User, Company).join(User, Contact.user_id == User.id).join(Company, Contact.company_id == Company.id)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    if company_id:
        query = query.filter(Contact.company_id == company_id)
        
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Contact.status == status_filter.upper())
        
    total_count = query.count()
    results = query.order_by(desc(Contact.created_at)).offset(skip).limit(limit).all()
    
    items = []
    for contact, user, company in results:
        items.append(ContactResponse(
            id=contact.id,
            user_id=user.id,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            email=user.email,
            phone_number=user.phone_number,
            position=contact.position,
            is_primary_contact=contact.is_primary_contact,
            company_id=contact.company_id,
            status=contact.status,
            company_name=company.company_name,
            created_at=contact.created_at,
            updated_at=contact.updated_at
        ))
        
    return PaginatedContactResponse(total_count=total_count, items=items)

@router.post("", response_model=ContactResponse)
def create_contact(
    payload: ContactCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify email is unique
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
        
    # Get Role
    role = db.query(Role).filter(Role.code == "COMPANY_CONTACT").first()
    if not role:
        raise HTTPException(status_code=500, detail="COMPANY_CONTACT role not found in database.")
        
    # Verify Company
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found.")
        
    # Create User with a random password — a reset link is sent via email
    import secrets as _secrets
    random_password = _secrets.token_urlsafe(16)
    new_user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone_number=payload.phone_number,
        password_hash=get_password_hash(random_password),
        role_id=role.id,
        status="ACTIVE",
        first_login=True
    )
    db.add(new_user)
    db.flush()
    
    # Create Contact
    new_contact = Contact(
        user_id=new_user.id,
        company_id=payload.company_id,
        position=payload.position,
        is_primary_contact=payload.is_primary_contact,
        status="ACTIVE"
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    db.refresh(new_user)
    
    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Contact Created',
        entity_type='Contact',
        entity_id=new_contact.id,
        new_values=payload.model_dump(),
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()

    # Send a password-reset email so the contact can set their own password
    from app.core.config import settings as cfg
    from app.core.redis import set_reset_token
    from app.tasks.email_tasks import send_password_reset_email
    reset_token = _secrets.token_urlsafe(32)
    set_reset_token(reset_token, new_user.id)
    reset_link = f"{cfg.FRONTEND_URL}/reset-password?token={reset_token}"
    send_password_reset_email(str(new_user.email), reset_link, "fr")
    
    return ContactResponse(
        id=new_contact.id,
        user_id=new_user.id,
        first_name=new_user.first_name or "",
        last_name=new_user.last_name or "",
        email=new_user.email,
        phone_number=new_user.phone_number,
        position=new_contact.position,
        is_primary_contact=new_contact.is_primary_contact,
        company_id=new_contact.company_id,
        status=new_contact.status,
        company_name=company.company_name,
        created_at=new_contact.created_at,
        updated_at=new_contact.updated_at
    )

@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    user = db.query(User).filter(User.id == contact.user_id).first()
    
    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use.")
        user.email = payload.email
        
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
        
    if payload.position is not None:
        contact.position = payload.position
    if payload.is_primary_contact is not None:
        contact.is_primary_contact = payload.is_primary_contact
    if payload.company_id is not None:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=400, detail="Company not found")
        contact.company_id = payload.company_id
        
    old_values = {}
    new_values = {}
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        # Just grab basic changes
        old_values = {'email': user.email, 'position': contact.position, 'is_primary': contact.is_primary_contact}
        new_values = update_data
        
    db.commit()
    db.refresh(contact)
    db.refresh(user)
    
    if update_data:
        audit_entry = AuditLog(
            user_id=current_user.id,
            action='Contact Updated',
            entity_type='Contact',
            entity_id=contact.id,
            old_values={k: str(v) for k,v in old_values.items()},
            new_values={k: str(v) for k,v in new_values.items()},
            ip_address=get_client_ip(request)
        )
        db.add(audit_entry)
        db.commit()
    
    company = db.query(Company).filter(Company.id == contact.company_id).first()
    
    return ContactResponse(
        id=contact.id,
        user_id=user.id,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        email=user.email,
        phone_number=user.phone_number,
        position=contact.position,
        is_primary_contact=contact.is_primary_contact,
        company_id=contact.company_id,
        status=contact.status,
        company_name=company.company_name,
        created_at=contact.created_at,
        updated_at=contact.updated_at
    )

@router.patch("/{contact_id}/status")
def toggle_contact_status(
    contact_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    user = db.query(User).filter(User.id == contact.user_id).first()
    
    if contact.status == "ACTIVE":
        contact.status = "INACTIVE"
        if user:
            user.status = "DISABLED"
    else:
        contact.status = "ACTIVE"
        if user:
            user.status = "ACTIVE"
            
    db.commit()
    
    action_str = 'Contact Enabled' if contact.status == 'ACTIVE' else 'Contact Disabled'
    audit_entry = AuditLog(
        user_id=current_user.id,
        action=action_str,
        entity_type='Contact',
        entity_id=contact.id,
        old_values={'status': "ACTIVE" if contact.status == "INACTIVE" else "INACTIVE"},
        new_values={'status': contact.status},
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()
    
    return {"message": "Status updated successfully", "status": contact.status}
