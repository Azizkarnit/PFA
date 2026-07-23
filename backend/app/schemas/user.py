from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

class UserAdminResponse(BaseModel):
    id: int
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    status: str
    role_name: str
    role_code: Optional[str] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedUserResponse(BaseModel):
    total_count: int
    items: List[UserAdminResponse]

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role_id: int

class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    role_id: int

class UserStatusUpdate(BaseModel):
    status: str

class LockedAccountResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    locked_since: datetime
    unlocks_at: datetime

    model_config = ConfigDict(from_attributes=True)
