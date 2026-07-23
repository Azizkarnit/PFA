import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.worksheet.worksheet import Worksheet
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, cast, String

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import PaginatedAuditLogResponse
from app.tasks.export_tasks import export_audit_logs_task
from app.core.celery_app import celery_app
from fastapi.responses import StreamingResponse, FileResponse
from celery.result import AsyncResult
from fastapi import APIRouter
import os

router = APIRouter()

def get_filtered_query(
    db: Session,
    search: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    query = db.query(AuditLog).outerjoin(User, AuditLog.user_id == User.id).options(joinedload(AuditLog.user))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
                AuditLog.entity_type.ilike(search_term),
                cast(AuditLog.id, String).ilike(search_term)
            )
        )
    
    if action:
        query = query.filter(AuditLog.action == action)
        
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
        
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
        
    return query

@router.get("/", response_model=PaginatedAuditLogResponse)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = get_filtered_query(db, search, action, date_from, date_to)
    total_count = query.count()
    items = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    return {"total_count": total_count, "items": items}

@router.post("/export")
def export_audit_logs_trigger(
    search: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    date_from_str = date_from.isoformat() if date_from else None
    date_to_str = date_to.isoformat() if date_to else None
    
    task = export_audit_logs_task.delay(
        search=search, 
        action=action, 
        date_from_str=date_from_str, 
        date_to_str=date_to_str
    )
    return {"task_id": task.id}

@router.get("/export/status/{task_id}")
def check_export_status(task_id: str, current_user = Depends(get_current_user)):
    result = AsyncResult(task_id, app=celery_app)
    return {"status": result.status}

@router.get("/export/download/{task_id}")
def download_export_file(task_id: str, current_user = Depends(get_current_user)):
    result = AsyncResult(task_id, app=celery_app)
    if result.status != "SUCCESS":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File is not ready yet.")
        
    file_path = result.result.get("file_path")
    if not file_path or not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found.")
        
    return FileResponse(
        path=file_path,
        filename=f"audit_logs_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
