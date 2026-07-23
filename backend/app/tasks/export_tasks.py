import os
import openpyxl
from openpyxl.styles import Font, Alignment
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, desc, cast, String
import datetime

@celery_app.task
def export_audit_logs_task(search=None, action=None, date_from_str=None, date_to_str=None):
    db = SessionLocal()
    try:
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
            
        if date_from_str:
            query = query.filter(AuditLog.created_at >= datetime.datetime.fromisoformat(date_from_str))
            
        if date_to_str:
            query = query.filter(AuditLog.created_at <= datetime.datetime.fromisoformat(date_to_str))
            
        # Create an Excel workbook efficiently
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet("Audit Logs")
        
        headers = ["Audit ID", "Date & Time", "User", "Action", "Item", "IP Address"]
        ws.append(headers)
        
        # Batch fetching to avoid memory explosion
        items = query.order_by(desc(AuditLog.created_at)).yield_per(1000)
        
        for item in items:
            user_name = f"{item.user.first_name} {item.user.last_name}" if item.user else "System"
            ws.append([
                item.id,
                item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                user_name,
                item.action,
                item.entity_type,
                item.ip_address or "N/A"
            ])
            
        os.makedirs("uploads", exist_ok=True)
        task_id = export_audit_logs_task.request.id
        file_path = os.path.join("uploads", f"audit_logs_{task_id}.xlsx")
        
        wb.save(file_path)
        return {"file_path": file_path}
    finally:
        db.close()
