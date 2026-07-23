import datetime
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.questionnaire_token import QuestionnaireToken
from app.models.collection_tracking import CollectionTracking
from app.models.survey_passage import SurveyPassage

logger = logging.getLogger(__name__)
router = APIRouter()

# ── API Key Dependency ────────────────────────────────────────────────────────
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.EXT_TO_PFA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API key"
        )
    return x_api_key

# ── Schemas ───────────────────────────────────────────────────────────────────
class ResolveTokenRequest(BaseModel):
    uuid: str

class ResolveTokenResponse(BaseModel):
    valid: bool
    passage_id: int
    company_id: int
    company_name: str
    survey_name: str
    closing_date: datetime.datetime
    questions: List[dict]

class StatusUpdateRequest(BaseModel):
    uuid: str
    status: str  # IN_PROGRESS or COMPLETED
    submitted_at: Optional[datetime.datetime] = None

# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/resolve", response_model=ResolveTokenResponse)
def resolve_uuid_token(
    payload: ResolveTokenRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    token_obj = db.query(QuestionnaireToken).filter(
        QuestionnaireToken.token == payload.uuid
    ).first()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UUID token not found or invalid"
        )
        
    passage = token_obj.passage
    company = token_obj.company
    survey = passage.survey
    
    # Enforce closing date check on token resolution
    if passage.closing_date < datetime.datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The survey passage has closed and no longer accepts connections."
        )
        
    # Define hardcoded questions (Phase 1)
    questions = [
        { "id": 1, "order": 1, "text": "Chiffre d'affaires annuel (DZD)", "type": "NUMBER", "required": True },
        { "id": 2, "order": 2, "text": "Nombre d'employés permanents", "type": "NUMBER", "required": True },
        { "id": 3, "order": 3, "text": "Commentaires ou suggestions sur la collecte", "type": "TEXT", "required": False }
    ]
    
    # Ensure CollectionTracking is set to IN_PROGRESS upon first resolution
    tracking = db.query(CollectionTracking).filter(
        CollectionTracking.passage_id == passage.id,
        CollectionTracking.company_id == company.id
    ).first()
    
    if not tracking:
        tracking = CollectionTracking(
            passage_id=passage.id,
            company_id=company.id,
            status="IN_PROGRESS",
            first_access_at=datetime.datetime.now(),
            last_activity_at=datetime.datetime.now()
        )
        db.add(tracking)
    else:
        if tracking.status == "NOT_STARTED":
            tracking.status = "IN_PROGRESS"
            tracking.first_access_at = datetime.datetime.now()
        tracking.last_activity_at = datetime.datetime.now()
        
    db.commit()
    
    return ResolveTokenResponse(
        valid=True,
        passage_id=passage.id,
        company_id=company.id,
        company_name=company.company_name or "",
        survey_name=survey.name or "",
        closing_date=passage.closing_date,
        questions=questions
    )

@router.post("/status-update")
def update_questionnaire_status(
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    if payload.status not in ["IN_PROGRESS", "COMPLETED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status parameter. Must be IN_PROGRESS or COMPLETED."
        )

    token_obj = db.query(QuestionnaireToken).filter(
        QuestionnaireToken.token == payload.uuid
    ).first()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UUID token not found"
        )
        
    passage = token_obj.passage
    
    # Enforce closing date check on status updates
    if passage.closing_date < datetime.datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The survey passage has closed. No updates are allowed."
        )
        
    tracking = db.query(CollectionTracking).filter(
        CollectionTracking.passage_id == token_obj.passage_id,
        CollectionTracking.company_id == token_obj.company_id
    ).first()
    
    if not tracking:
        tracking = CollectionTracking(
            passage_id=token_obj.passage_id,
            company_id=token_obj.company_id,
            status="NOT_STARTED"
        )
        db.add(tracking)
        db.flush()
        
    if payload.status == "IN_PROGRESS":
        if tracking.status == "NOT_STARTED":
            tracking.status = "IN_PROGRESS"
            tracking.first_access_at = datetime.datetime.now()
        tracking.last_activity_at = datetime.datetime.now()
    elif payload.status == "COMPLETED":
        tracking.status = "COMPLETED"
        tracking.submitted_at = payload.submitted_at or datetime.datetime.now()
        tracking.last_activity_at = datetime.datetime.now()
        
    db.commit()
    
    # Trigger notifications for Survey Manager(s) on completion
    if payload.status == "COMPLETED":
        try:
            from app.core.notification_service import notify_survey_admins_for_survey, create_notification
            survey = passage.survey
            company = token_obj.company
            
            title = "Survey Submitted"
            message = f"The company '{company.company_name}' has submitted their questionnaire for the survey '{survey.name}' (Passage {passage.year}/P{passage.passage_number})."
            action_url = f"/admin/surveys/{survey.id}"
            
            # Notify assigned admins
            notify_survey_admins_for_survey(
                db=db,
                survey_id=survey.id,
                title=title,
                message=message,
                type="INFO",
                action_url=action_url
            )
            
            # Notify creator of the survey if they aren't explicitly assigned and are not an ACCOUNT_MANAGER
            survey_creator_id = survey.created_by
            from app.models.user import User
            from app.models.role import Role
            creator_is_account_manager = (
                db.query(User)
                .join(Role, Role.id == User.role_id)
                .filter(User.id == survey_creator_id, Role.code == "ACCOUNT_MANAGER")
                .count() > 0
            )
            
            if not creator_is_account_manager:
                from app.models.survey_assignment import SurveyAssignment
                creator_assigned = db.query(SurveyAssignment).filter(
                    SurveyAssignment.survey_id == survey.id,
                    SurveyAssignment.user_id == survey_creator_id
                ).first()
                
                if not creator_assigned:
                    create_notification(
                        db=db,
                        user_id=survey_creator_id,
                        title=title,
                        message=message,
                        type="INFO",
                        action_url=action_url
                    )
        except Exception as e:
            logger.error(f"Error sending submit notification: {e}")
            
    return {"message": "Status updated successfully", "status": payload.status}
