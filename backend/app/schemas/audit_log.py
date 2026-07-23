from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AuditLogUserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    user: Optional[AuditLogUserResponse] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedAuditLogResponse(BaseModel):
    items: List[AuditLogResponse]
    total_count: int
