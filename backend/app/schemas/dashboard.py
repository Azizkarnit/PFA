from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class LockedAccount(BaseModel):
    id: int
    name: str
    email: str
    locked_since: datetime

    model_config = ConfigDict(from_attributes=True)

class RecentActivity(BaseModel):
    id: int
    type: str # e.g., 'login', 'create_company', 'update_survey'
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class RoleDistribution(BaseModel):
    role_name: str
    count: int
    percentage: float

class SectorDistribution(BaseModel):
    sector_name: str
    count: int

class StatusDistribution(BaseModel):
    status: str
    count: int

class GrowthPoint(BaseModel):
    month: str
    count: int

class RecentSurvey(BaseModel):
    id: int
    code: str
    name: str
    periodicity: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecentContact(BaseModel):
    id: int
    name: str
    email: str
    company_name: Optional[str]
    position: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardStatsResponse(BaseModel):
    total_users: int
    active_users: int
    active_companies: int
    locked_accounts_count: int
    total_surveys: int
    locked_accounts: List[LockedAccount]
    recent_activities: List[RecentActivity]
    role_distribution: List[RoleDistribution]
    companies_by_sector: List[SectorDistribution] = []
    companies_by_status: List[StatusDistribution] = []
    companies_growth: List[GrowthPoint] = []
    surveys_growth: List[GrowthPoint] = []
    total_contacts: Optional[int] = None
    contacts_growth: List[GrowthPoint] = []
    recent_contacts: List[RecentContact] = []
    
    # Survey Admin specific
    my_surveys_count: Optional[int] = None
    my_active_passages_count: Optional[int] = None
    my_total_passages_count: Optional[int] = None
    my_monitored_companies_count: Optional[int] = None
    my_recent_surveys: Optional[List[RecentSurvey]] = None
