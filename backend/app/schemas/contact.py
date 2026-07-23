from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    position: Optional[str] = None
    is_primary_contact: bool = False
    company_id: int

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    position: Optional[str] = None
    is_primary_contact: Optional[bool] = None
    company_id: Optional[int] = None
    status: Optional[str] = None # "ACTIVE" or "INACTIVE"

class ContactResponse(ContactBase):
    id: int
    user_id: int
    status: str
    company_name: str # Joined field
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedContactResponse(BaseModel):
    total_count: int
    items: list[ContactResponse]
