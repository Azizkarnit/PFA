"""
Portal API — endpoints for Company Contact users.
"""
import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.company import Company
from app.models.survey import Survey
from app.models.survey_passage import SurveyPassage
from app.models.survey_assignment import SurveyAssignment
from app.models.sample import Sample
from app.models.sample_company import SampleCompany
from app.models.collection_tracking import CollectionTracking
from app.models.survey_result_file import SurveyResultFile
from app.models.sector import Sector
from app.models.questionnaire_token import QuestionnaireToken
from app.core.config import settings

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class PortalSurveySummary(BaseModel):
    id: int
    code: str
    name: str
    periodicity: Optional[str]
    status: str           # survey status (ACTIVE / INACTIVE / ARCHIVED)
    visit_status: str     # IN_PROGRESS | NOT_STARTED | SUBMITTED
    passage_id: Optional[int]
    passage_year: Optional[int]
    passage_number: Optional[int]
    closing_date: Optional[datetime.datetime]
    questionnaire_pdf_path: Optional[str]


class PortalResultFile(BaseModel):
    id: int
    survey_id: int
    survey_name: str
    file_name: str
    file_path: str
    file_type: str
    uploaded_at: datetime.datetime



class PortalProfileResponse(BaseModel):
    first_name: str
    last_name: str
    position: Optional[str]
    company_name: str
    company_identifier: str
    sector_name: Optional[str]
    email: str
    preferred_language: str

class PortalProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    position: Optional[str]
    preferred_language: str


class PortalHomeResponse(BaseModel):
    first_name: str
    last_name: str
    company_name: str
    position: Optional[str]
    assigned_surveys_count: int
    pending_actions_count: int
    surveys: List[PortalSurveySummary]
    results: List[PortalResultFile]


class PortalSurveyLinkResponse(BaseModel):
    url: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_contact_or_403(current_user: User, db: Session):
    if not current_user.role or current_user.role.code != "COMPANY_CONTACT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access restricted to Company Contacts.")
    contact: Any = current_user.contact
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Contact profile not found.")
    return contact


def _get_company_surveys(company_id: int, db: Session) -> List[Any]:
    """
    Get all active passages whose sample includes the given company.
    Returns list of (Survey, SurveyPassage) tuples.
    """
    # find all sample_company rows for this company
    sample_company_rows = db.query(SampleCompany).filter(
        SampleCompany.company_id == company_id
    ).all()

    sample_ids = [sc.sample_id for sc in sample_company_rows]
    if not sample_ids:
        return []

    # find all passages that use those samples
    passages = (
        db.query(SurveyPassage)
        .join(Sample, Sample.passage_id == SurveyPassage.id)
        .filter(Sample.id.in_(sample_ids))
        .filter(SurveyPassage.status == "OPEN")
        .all()
    )

    results = []
    seen_survey_ids = set()
    for passage in passages:
        survey = db.query(Survey).filter(Survey.id == passage.survey_id).first()
        if survey and survey.id not in seen_survey_ids:
            seen_survey_ids.add(survey.id)
            results.append((survey, passage))

    return results


def _visit_status(company_id: int, passage: Any, db: Session) -> str:
    """
    Determine visit status based on CollectionTracking.status.
    - NOT_STARTED: no tracking row or status = NOT_STARTED
    - IN_PROGRESS: status = IN_PROGRESS
    - COMPLETED: status = COMPLETED
    """
    tracking = db.query(CollectionTracking).filter(
        CollectionTracking.passage_id == passage.id,
        CollectionTracking.company_id == company_id,
    ).first()
    if not tracking:
        return "NOT_STARTED"
    tracking_any: Any = tracking
    return tracking_any.status  # NOT_STARTED | IN_PROGRESS | COMPLETED


def _get_results_for_company(company: Any, db: Session) -> List[Any]:
    """
    Get result files published for the sector of the contact's company.
    """
    company_obj: Any = company
    sector_id = company_obj.sector_id
    if not sector_id:
        return []
    files = (
        db.query(SurveyResultFile)
        .filter(SurveyResultFile.sector_id == sector_id)
        .order_by(SurveyResultFile.uploaded_at.desc())
        .limit(3)
        .all()
    )
    return files


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/home", response_model=PortalHomeResponse)
def get_portal_home(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = _get_contact_or_403(current_user, db)
    contact_any: Any = contact
    company = db.query(Company).filter(Company.id == contact_any.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    company_any: Any = company
    survey_passage_pairs = _get_company_surveys(company_any.id, db)

    survey_summaries: List[PortalSurveySummary] = []
    for survey, passage in survey_passage_pairs[:3]:
        s: Any = survey
        p: Any = passage
        v_status = _visit_status(company_any.id, passage, db)
        questionnaires = getattr(p, 'questionnaires', [])
        pdf_path = None
        if questionnaires:
            latest_q = sorted(questionnaires, key=lambda q: q.id, reverse=True)[0]
            pdf_path = latest_q.questionnaire_pdf_path

        survey_summaries.append(PortalSurveySummary(
            id=s.id,
            code=s.code,
            name=s.name,
            periodicity=s.periodicity,
            status=s.status,
            visit_status=v_status,
            passage_id=p.id,
            passage_year=p.year,
            passage_number=p.passage_number,
            closing_date=p.closing_date,
            questionnaire_pdf_path=pdf_path,
        ))

    pending_count = sum(1 for ss in survey_summaries if ss.visit_status == "NOT_STARTED")

    result_files = _get_results_for_company(company, db)
    result_summaries: List[PortalResultFile] = []
    for rf in result_files:
        rf_any: Any = rf
        survey = db.query(Survey).filter(Survey.id == rf_any.survey_id).first()
        survey_name = survey.name if survey else "Unknown Survey"
        result_summaries.append(PortalResultFile(
            id=rf_any.id,
            survey_id=rf_any.survey_id,
            survey_name=survey_name,
            file_name=rf_any.file_name,
            file_path=rf_any.file_path,
            file_type=rf_any.file_type,
            uploaded_at=rf_any.uploaded_at,
        ))

    user_any: Any = current_user
    return PortalHomeResponse(
        first_name=user_any.first_name or "",
        last_name=user_any.last_name or "",
        company_name=company_any.company_name or "",
        position=contact_any.position,
        assigned_surveys_count=len(survey_passage_pairs),
        pending_actions_count=pending_count,
        surveys=survey_summaries,
        results=result_summaries,
    )


@router.get("/surveys", response_model=List[PortalSurveySummary])
def get_portal_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = _get_contact_or_403(current_user, db)
    contact_any: Any = contact
    company = db.query(Company).filter(Company.id == contact_any.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    company_any: Any = company
    survey_passage_pairs = _get_company_surveys(company_any.id, db)

    survey_summaries: List[PortalSurveySummary] = []
    for survey, passage in survey_passage_pairs:
        s: Any = survey
        p: Any = passage
        v_status = _visit_status(company_any.id, passage, db)
        questionnaires = getattr(p, 'questionnaires', [])
        pdf_path = None
        if questionnaires:
            latest_q = sorted(questionnaires, key=lambda q: q.id, reverse=True)[0]
            pdf_path = latest_q.questionnaire_pdf_path

        survey_summaries.append(PortalSurveySummary(
            id=s.id,
            code=s.code,
            name=s.name,
            periodicity=s.periodicity,
            status=s.status,
            visit_status=v_status,
            passage_id=p.id,
            passage_year=p.year,
            passage_number=p.passage_number,
            closing_date=p.closing_date,
            questionnaire_pdf_path=pdf_path,
        ))

    return survey_summaries


@router.get("/results", response_model=List[PortalResultFile])
def get_portal_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = _get_contact_or_403(current_user, db)
    contact_any: Any = contact
    company = db.query(Company).filter(Company.id == contact_any.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    company_obj: Any = company
    sector_id = company_obj.sector_id
    if not sector_id:
        return []

    # Get all results without limit
    files = (
        db.query(SurveyResultFile)
        .filter(SurveyResultFile.sector_id == sector_id)
        .order_by(SurveyResultFile.uploaded_at.desc())
        .all()
    )

    result_summaries: List[PortalResultFile] = []
    for rf in files:
        rf_any: Any = rf
        survey = db.query(Survey).filter(Survey.id == rf_any.survey_id).first()
        survey_name = survey.name if survey else "Unknown Survey"
        result_summaries.append(PortalResultFile(
            id=rf_any.id,
            survey_id=rf_any.survey_id,
            survey_name=survey_name,
            file_name=rf_any.file_name,
            file_path=rf_any.file_path,
            file_type=rf_any.file_type,
            uploaded_at=rf_any.uploaded_at,
        ))

    return result_summaries


@router.get("/profile", response_model=PortalProfileResponse)
def get_portal_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = _get_contact_or_403(current_user, db)
    company = contact.company
    sector_name = company.sector.name if company.sector else None

    return PortalProfileResponse(
        first_name=current_user.first_name or "",
        last_name=current_user.last_name or "",
        position=contact.position,
        company_name=company.company_name,
        company_identifier=company.identifier,
        sector_name=sector_name,
        email=current_user.email,
        preferred_language=current_user.preferred_language or "en"
    )

@router.put("/profile", response_model=PortalProfileResponse)
def update_portal_profile(
    data: PortalProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = _get_contact_or_403(current_user, db)
    
    current_user.first_name = data.first_name
    current_user.last_name = data.last_name
    current_user.preferred_language = data.preferred_language
    
    contact.position = data.position
    
    db.commit()
    db.refresh(current_user)
    db.refresh(contact)
    
    company = contact.company
    sector_name = company.sector.name if company.sector else None
    
    return PortalProfileResponse(
        first_name=current_user.first_name or "",
        last_name=current_user.last_name or "",
        position=contact.position,
        company_name=company.company_name,
        company_identifier=company.identifier,
        sector_name=sector_name,
        email=current_user.email,
        preferred_language=current_user.preferred_language or "en"
    )


@router.get("/survey-link", response_model=PortalSurveyLinkResponse)
def get_portal_survey_link(
    passage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = _get_contact_or_403(current_user, db)
    # Check if a token already exists
    token_obj = db.query(QuestionnaireToken).filter(
        QuestionnaireToken.contact_id == contact.id,
        QuestionnaireToken.passage_id == passage_id
    ).first()
    
    # Fallback to create one on the fly if invitations were bypassed or token missing
    if not token_obj:
        import uuid
        token_uuid = str(uuid.uuid4())
        token_obj = QuestionnaireToken(
            token=token_uuid,
            contact_id=contact.id,
            company_id=contact.company_id,
            passage_id=passage_id
        )
        db.add(token_obj)
        db.commit()
        db.refresh(token_obj)
        
    url = f"{settings.EXT_APP_URL}/?uuid={token_obj.token}"
    return PortalSurveyLinkResponse(url=url)

