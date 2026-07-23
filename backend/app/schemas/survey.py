from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime



# ─── Assigned Admin ────────────────────────────────────────────────────────────

class AssignedAdminResponse(BaseModel):
    id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


# ─── Survey ───────────────────────────────────────────────────────────────────

class SurveyCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    periodicity: str
    assigned_admin_ids: List[int]
    status: str = "INACTIVE"

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Survey code cannot be empty.")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"ACTIVE", "INACTIVE", "ARCHIVED"}
        if v.upper() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.upper()

    @field_validator("periodicity")
    @classmethod
    def valid_periodicity(cls, v: str) -> str:
        allowed = {"ANNUAL", "MONTHLY", "QUARTERLY", "SEMI_ANNUAL", "BIENNIAL", "CUSTOM"}
        if v.upper() not in allowed:
            raise ValueError(f"Periodicity must be one of {allowed}")
        return v.upper()


class SurveyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    periodicity: Optional[str] = None
    assigned_admin_ids: Optional[List[int]] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"ACTIVE", "INACTIVE", "ARCHIVED"}
        if v.upper() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.upper()

    @field_validator("periodicity")
    @classmethod
    def valid_periodicity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"ANNUAL", "MONTHLY", "QUARTERLY", "SEMI_ANNUAL", "BIENNIAL", "CUSTOM"}
        if v.upper() not in allowed:
            raise ValueError(f"Periodicity must be one of {allowed}")
        return v.upper()


class SurveyResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    periodicity: str
    status: str
    assigned_admins: List[AssignedAdminResponse] = []
    passage_count: int = 0
    last_passage_year: Optional[int] = None
    last_passage_number: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaginatedSurveyResponse(BaseModel):
    total_count: int
    items: List[SurveyResponse]


# ─── Passage ──────────────────────────────────────────────────────────────────

class PassageCreate(BaseModel):
    year: int
    passage_number: int
    opening_date: datetime
    closing_date: datetime

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("Year must be between 2000 and 2100.")
        return v

    @field_validator("passage_number")
    @classmethod
    def valid_passage_number(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Passage number must be >= 1.")
        return v


class PassageUpdate(BaseModel):
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    status: Optional[str] = None


class PassageResponse(BaseModel):
    id: int
    survey_id: int
    year: int
    passage_number: int
    opening_date: datetime
    closing_date: datetime
    status: str
    company_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaginatedPassageResponse(BaseModel):
    total_count: int
    items: List[PassageResponse]


# ─── Questionnaire ────────────────────────────────────────────────────────────

class QuestionnaireCreate(BaseModel):
    questionnaire_url: Optional[str] = None
    version: str = "1.0"


class QuestionnaireResponse(BaseModel):
    id: int
    passage_id: int
    questionnaire_url: Optional[str] = None
    questionnaire_pdf_path: Optional[str] = None
    version: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Sample ───────────────────────────────────────────────────────────────────

class SampleCompanyInfo(BaseModel):
    id: int
    identifier: str
    company_name: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class SampleResponse(BaseModel):
    id: int
    passage_id: int
    total_companies: int
    uploaded_by: int
    uploader_name: Optional[str] = None
    created_at: datetime
    companies: List[SampleCompanyInfo] = []
    model_config = ConfigDict(from_attributes=True)


# ─── Monitoring ───────────────────────────────────────────────────────────────

class MonitoringStats(BaseModel):
    passage_id: int
    passage_year: int
    passage_number: int
    passage_status: str
    total_companies: int
    not_started: int
    in_progress: int
    completed: int
    completion_pct: float


class SurveyMonitoringResponse(BaseModel):
    survey_id: int
    total_passages: int
    total_companies_all_passages: int
    passages: List[MonitoringStats]


# ─── Result Files ─────────────────────────────────────────────────────────────

class ResultFileResponse(BaseModel):
    id: int
    survey_id: int
    sector_id: int
    sector_name: Optional[str] = None
    file_name: str
    file_path: str
    file_type: str
    uploaded_by: int
    uploader_name: Optional[str] = None
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)
