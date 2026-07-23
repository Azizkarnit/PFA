from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import cast
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.survey import Survey
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.sector import Sector
from app.models.survey_assignment import SurveyAssignment
from app.models.survey_passage import SurveyPassage
from app.models.sample import Sample
from app.models.sample_company import SampleCompany
from app.models.contact import Contact
from app.schemas.dashboard import DashboardStatsResponse, LockedAccount, RecentActivity, RoleDistribution, SectorDistribution, StatusDistribution, GrowthPoint, RecentSurvey, RecentContact
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)   # ← authentication required
):
    # 1. Total counts
    active_users = db.query(func.count(User.id)).filter(User.status == "ACTIVE").scalar() or 0
    active_companies = db.query(func.count(Company.id)).filter(Company.status == "ACTIVE").scalar() or 0
    total_surveys = db.query(func.count(Survey.id)).scalar() or 0

    # 2. Locked accounts — count from Redis (the authoritative lock store)
    from app.core.redis import get_all_locked_accounts
    locked_redis = get_all_locked_accounts()
    locked_accounts_count = len(locked_redis)

    # Build locked account details (latest 5)
    locked_accounts = []
    if locked_redis:
        user_ids = [item["user_id"] for item in locked_redis[:5]]
        locked_users = db.query(User).filter(User.id.in_(user_ids)).all()
        now = datetime.now()
        for u in locked_users:
            lock_info = next((item for item in locked_redis if item["user_id"] == u.id), None)
            name = f"{u.first_name} {u.last_name}".strip() if u.first_name and u.last_name else str(u.email).split('@')[0]
            locked_since = now
            if lock_info:
                ttl = lock_info["ttl"]
                duration = lock_info["duration"]
                unlocks_at = now + __import__("datetime").timedelta(seconds=ttl)
                locked_since = unlocks_at - __import__("datetime").timedelta(seconds=duration)
            locked_accounts.append(
                LockedAccount(
                    id=cast(int, u.id),
                    name=name,
                    email=cast(str, u.email),
                    locked_since=cast(datetime, locked_since)
                )
            )

    # 3. Role distribution
    total_users = db.query(func.count(User.id)).scalar() or 1  # avoid division by zero
    role_counts = db.query(Role.name, func.count(User.id)).join(User).group_by(Role.name).all()

    role_distribution = [
        RoleDistribution(
            role_name=role_name,
            count=count,
            percentage=round((count / total_users) * 100, 1)
        )
        for role_name, count in role_counts
    ]

    # 4. Recent Activity from Audit Logs
    recent_logs = (
        db.query(AuditLog, User)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(4)
        .all()
    )
    recent_activities = []
    for log, user in recent_logs:
        icon_type = "login" if log.action == "LOGIN" else "edit_document"
        name = "System"
        if user:
            name = f"{user.first_name} {user.last_name}".strip() if user.first_name and user.last_name else str(user.email).split('@')[0]

        action_str = str(log.action)
        if action_str == "LOGIN":
            details = f"{name} logged in from IP {log.ip_address or 'Unknown'}."
        elif action_str == "UPDATE_PROFILE":
            details = f"{name} updated their profile settings."
        else:
            action_formatted = action_str.replace('_', ' ').lower()
            details = f"{name} performed {action_formatted} on {log.entity_type}."
            if log.ip_address:
                details += f" (IP: {log.ip_address})"

        recent_activities.append(
            RecentActivity(
                id=cast(int, log.id),
                type=icon_type,
                description=details,
                timestamp=cast(datetime, log.created_at)
            )
        )


    # 5. Charts Aggregations
    # Companies by Sector
    sector_dist = db.query(Sector.name, func.count(Company.id)).join(Company).group_by(Sector.name).all()
    companies_by_sector = [SectorDistribution(sector_name=s[0], count=s[1]) for s in sector_dist]

    # Companies by Status
    status_dist = db.query(Company.status, func.count(Company.id)).group_by(Company.status).all()
    companies_by_status = [StatusDistribution(status=s[0], count=s[1]) for s in status_dist]

    # Generate last 6 months keys
    now = datetime.now()
    last_6_months = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        if m <= 0:
            m += 12
            y -= 1
        last_6_months.append(f"{y}-{m:02d}")

    # Companies Growth (Last 6 months)
    companies_growth_raw = db.query(
        func.date_format(Company.created_at, '%Y-%m').label('month'), 
        func.count(Company.id)
    ).group_by('month').all()
    comp_dict = {g[0]: g[1] for g in companies_growth_raw}
    companies_growth = [GrowthPoint(month=m, count=comp_dict.get(m, 0)) for m in last_6_months]

    # Surveys Growth (Last 6 months)
    surveys_growth_raw = db.query(
        func.date_format(Survey.created_at, '%Y-%m').label('month'), 
        func.count(Survey.id)
    ).group_by('month').all()
    surv_dict = {g[0]: g[1] for g in surveys_growth_raw}
    surveys_growth = [GrowthPoint(month=m, count=surv_dict.get(m, 0)) for m in last_6_months]

    # Contact specific logic
    total_contacts = db.query(func.count(User.id)).join(Role).filter(Role.code == "COMPANY_CONTACT").scalar() or 0

    contacts_growth_raw = db.query(
        func.date_format(User.created_at, '%Y-%m').label('month'), 
        func.count(User.id)
    ).join(Role).filter(Role.code == "COMPANY_CONTACT").group_by('month').all()
    contact_dict = {g[0]: g[1] for g in contacts_growth_raw}
    contacts_growth = [GrowthPoint(month=m, count=contact_dict.get(m, 0)) for m in last_6_months]

    recent_contacts_query = db.query(User, Contact, Company).join(Contact, User.id == Contact.user_id).join(Company, Contact.company_id == Company.id).filter(User.role.has(code="COMPANY_CONTACT")).order_by(User.created_at.desc()).limit(5).all()
    recent_contacts = [
        RecentContact(
            id=u.id,
            name=f"{u.first_name} {u.last_name}".strip(),
            email=str(u.email),
            company_name=c.company_name,
            position=con.position,
            status=str(u.status),
            created_at=cast(datetime, u.created_at)
        )
        for u, con, c in recent_contacts_query
    ]

    # Survey Admin specific logic
    my_surveys_count = None
    my_active_passages_count = None
    my_total_passages_count = None
    my_monitored_companies_count = None
    my_recent_surveys = None

    if current_user.role.code == "SURVEY_ADMINISTRATOR":
        # Surveys assigned to the current user
        my_surveys_query = db.query(Survey).join(SurveyAssignment).filter(SurveyAssignment.user_id == current_user.id)
        my_surveys_count = my_surveys_query.count()

        # Active passages for those surveys
        my_active_passages_count = db.query(func.count(SurveyPassage.id))\
            .join(Survey, SurveyPassage.survey_id == Survey.id)\
            .join(SurveyAssignment, Survey.id == SurveyAssignment.survey_id)\
            .filter(SurveyAssignment.user_id == current_user.id, SurveyPassage.status == "OPEN")\
            .scalar() or 0
            
        # Total passages for those surveys
        my_total_passages_count = db.query(func.count(SurveyPassage.id))\
            .join(Survey, SurveyPassage.survey_id == Survey.id)\
            .join(SurveyAssignment, Survey.id == SurveyAssignment.survey_id)\
            .filter(SurveyAssignment.user_id == current_user.id)\
            .scalar() or 0
            
        # Unique monitored companies
        my_monitored_companies_count = db.query(func.count(func.distinct(SampleCompany.company_id)))\
            .join(Sample, SampleCompany.sample_id == Sample.id)\
            .join(SurveyPassage, Sample.passage_id == SurveyPassage.id)\
            .join(Survey, SurveyPassage.survey_id == Survey.id)\
            .join(SurveyAssignment, Survey.id == SurveyAssignment.survey_id)\
            .filter(SurveyAssignment.user_id == current_user.id)\
            .scalar() or 0

        # Recent 5 surveys assigned
        recent_assigned = my_surveys_query.order_by(SurveyAssignment.assigned_at.desc()).limit(5).all()
        my_recent_surveys = [
            RecentSurvey(
                id=s.id,
                code=s.code,
                name=s.name,
                periodicity=s.periodicity,
                status=s.status,
                created_at=s.created_at
            )
            for s in recent_assigned
        ]

    return DashboardStatsResponse(
        total_users=total_users,
        active_users=active_users,
        active_companies=active_companies,
        locked_accounts_count=locked_accounts_count,
        total_surveys=total_surveys,
        locked_accounts=locked_accounts,
        recent_activities=recent_activities,
        role_distribution=role_distribution,
        my_surveys_count=my_surveys_count,
        my_active_passages_count=my_active_passages_count,
        my_total_passages_count=my_total_passages_count,
        my_monitored_companies_count=my_monitored_companies_count,
        my_recent_surveys=my_recent_surveys,
        companies_by_sector=companies_by_sector,
        companies_by_status=companies_by_status,
        companies_growth=companies_growth,
        surveys_growth=surveys_growth,
        total_contacts=total_contacts,
        contacts_growth=contacts_growth,
        recent_contacts=recent_contacts
    )
