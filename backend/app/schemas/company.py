from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SectorBase(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)

class ActivityBase(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)

class CompanyBase(BaseModel):
    identifier: str
    company_name: str
    tax_number: Optional[str] = None
    address: Optional[str] = None
    governorate: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str

class CompanyCreate(BaseModel):
    identifier: str
    company_name: str
    tax_number: Optional[str] = None
    address: Optional[str] = None
    governorate: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    sector_id: int
    activity_id: int

class CompanyUpdate(BaseModel):
    identifier: Optional[str] = None
    company_name: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    governorate: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    sector_id: Optional[int] = None
    activity_id: Optional[int] = None

class CompanyResponse(CompanyBase):
    id: int
    sector: SectorBase
    activity: ActivityBase
    contacts_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedCompanyResponse(BaseModel):
    total_count: int
    items: list[CompanyResponse]

class ImportRowResult(BaseModel):
    row_number: int
    status: str  # "valid" | "error" | "warning"
    errors: list[str] = []
    warnings: list[str] = []
    data: dict = {}  # cleaned data ready for insert (only if status == "valid")

class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_count: int
    error_count: int
    warning_count: int
    rows: list[ImportRowResult]

class ImportConfirmRequest(BaseModel):
    session_id: str

class ImportConfirmResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = []