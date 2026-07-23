from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from app.core.utils import get_client_ip
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io, re
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import PatternFill, Font, Alignment
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.company import Company
from app.models.sector import Sector
from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.schemas.company import (
    CompanyResponse, PaginatedCompanyResponse, CompanyUpdate, CompanyCreate,
    SectorBase, ActivityBase,
    ImportRowResult, ImportPreviewResponse, ImportConfirmRequest, ImportConfirmResponse
)
from app.models.import_session import ImportSession, CompanyImportStaging
from app.tasks.import_tasks import process_excel_import
from sqlalchemy import or_
import os
import shutil

EXPECTED_COLUMNS = [
    "identifier", "company_name", "tax_number", "email",
    "phone", "address", "governorate", "postal_code", "sector", "activity"
]

def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def _clean(val) -> str:
    if val is None:
        return ""
    cleaned = str(val).strip()
    # If the cell literally contained the text "null", "n/a", etc, treat it as empty
    if cleaned.lower() in ["null", "n/a", "none", "nan", "-", "undefined"]:
        return ""
    return cleaned


router = APIRouter()

@router.get("/import/template")
def download_import_template(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Generate and return a ready-to-fill Excel template for company imports.
    Includes the correct headers, a sample valid row, and a hidden
    reference sheet listing valid sectors and activities from the DB.
    """
    sectors = db.query(Sector).all()
    activities = db.query(Activity).all()

    wb = openpyxl.Workbook()
    ws: Worksheet = wb.active  # type: ignore
    ws.title = "companies_import"

    # --- Header row ---
    headers = EXPECTED_COLUMNS
    header_fill = PatternFill(start_color="0B4F8A", end_color="0B4F8A", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    col_widths  = [18, 28, 18, 32, 22, 30, 16, 14, 22, 24]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[1].height = 28
    for i, w in enumerate(col_widths, start=1):
        from openpyxl.utils import get_column_letter
        ws.column_dimensions[get_column_letter(i)].width = w

    # --- Sample row ---
    sample_sector   = sectors[0].name_en   if sectors   else "Technology"
    sample_activity = activities[0].name_en if activities else "Software Development"
    sample_row = [
        "ENT-0001", "Example Company SARL", "1234567890",
        "contact@example.tn", "+216 71 100 200",
        "10 Rue de Carthage, Tunis", "Tunis", "1001",
        sample_sector, sample_activity
    ]
    sample_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    for col_idx, value in enumerate(sample_row, start=1):
        cell = ws.cell(row=2, column=col_idx, value=str(value))
        cell.fill = sample_fill

    ws.freeze_panes = "A2"

    # --- Reference sheet: valid sectors / activities ---
    ws_ref: Worksheet = wb.create_sheet("Reference (do not edit)") # type: ignore
    ws_ref.cell(1, 1, "Valid Sectors").font = Font(bold=True)
    ws_ref.cell(1, 2, "Valid Activities").font = Font(bold=True)
    for i, s in enumerate(sectors, start=2):
        ws_ref.cell(i, 1, str(s.name_en))
    for i, a in enumerate(activities, start=2):
        ws_ref.cell(i, 2, str(a.name_en))
    ws_ref.column_dimensions["A"].width = 30
    ws_ref.column_dimensions["B"].width = 30

    # --- Stream response ---
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="companies_import_template.xlsx"'}
    )

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company_in: CompanyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if db.query(Company).filter(Company.identifier == company_in.identifier).first():
        raise HTTPException(status_code=400, detail="Company with this identifier already exists")
    if company_in.email and db.query(Company).filter(Company.email == company_in.email).first():
        raise HTTPException(status_code=400, detail="Company with this email already exists")

    new_company = Company(
        **company_in.model_dump(),
        status="ACTIVE"
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    new_company.contacts_count = 0
    
    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Company Created',
        entity_type='Company',
        entity_id=new_company.id,
        new_values=company_in.model_dump(),
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()
    
    return new_company

@router.get("/sectors", response_model=List[SectorBase])
def get_sectors(db: Session = Depends(get_db)):
    return db.query(Sector).all()

@router.get("/activities", response_model=List[ActivityBase])
def get_activities(db: Session = Depends(get_db)):
    return db.query(Activity).all()

@router.get("/", response_model=PaginatedCompanyResponse)
def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    sector_id: Optional[int] = None,
    activity_id: Optional[int] = None,
    governorate: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Company)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.company_name.ilike(search_term),
                Company.identifier.ilike(search_term),
                Company.tax_number.ilike(search_term)
            )
        )
    
    if sector_id:
        query = query.filter(Company.sector_id == sector_id)
    if activity_id:
        query = query.filter(Company.activity_id == activity_id)
    if governorate:
        query = query.filter(Company.governorate == governorate)
    if status:
        query = query.filter(Company.status == status)

    total_count = query.count()
    items = query.order_by(Company.created_at.desc(), Company.id.desc()).offset(skip).limit(limit).all()
    
    for item in items:
        item.contacts_count = len(item.contacts)  # type: ignore

    return {"total_count": total_count, "items": items}

@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    old_values = {c.name: getattr(company, c.name) for c in company.__table__.columns if getattr(company, c.name) is not None}
    
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    new_values = {c.name: getattr(company, c.name) for c in company.__table__.columns if getattr(company, c.name) is not None}
    
    audit_entry = AuditLog(
        user_id=current_user.id,
        action='Company Updated',
        entity_type='Company',
        entity_id=company.id,
        old_values={k: str(v) for k, v in old_values.items() if k in update_data},
        new_values={k: str(v) for k, v in new_values.items() if k in update_data},
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()
    
    company.contacts_count = len(company.contacts)  # type: ignore
    return company

@router.patch("/{company_id}/status", response_model=CompanyResponse)
def update_company_status(
    company_id: int,
    request: Request,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if status not in ["ACTIVE", "INACTIVE"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    old_status = company.status
    company.status = status
    db.commit()
    db.refresh(company)
    
    action_str = 'Company Enabled' if status == 'ACTIVE' else 'Company Disabled'
    audit_entry = AuditLog(
        user_id=current_user.id,
        action=action_str,
        entity_type='Company',
        entity_id=company.id,
        old_values={'status': str(old_status)},
        new_values={'status': str(status)},
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    db.commit()
    
    company.contacts_count = len(company.contacts)  # type: ignore
    return company


@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start background validation of an uploaded .xlsx file.
    Returns a session ID to poll for status.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are supported.")

    os.makedirs("uploads", exist_ok=True)
    
    # Create an ImportSession
    session_record = ImportSession()
    db.add(session_record)
    db.commit()
    db.refresh(session_record)
    
    file_path = os.path.join("uploads", f"import_{session_record.id}.xlsx")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger Celery Task
    process_excel_import.delay(session_record.id, file_path)
    
    return {"session_id": session_record.id, "status": session_record.status}

@router.get("/import/session/{session_id}")
def get_import_session_status(session_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    session_record = db.query(ImportSession).filter(ImportSession.id == session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    return {
        "id": session_record.id,
        "status": session_record.status,
        "total_rows": session_record.total_rows,
        "valid_count": session_record.valid_count,
        "error_count": session_record.error_count,
        "warning_count": session_record.warning_count,
        "error_message": session_record.error_message
    }

@router.get("/import/staging/{session_id}")
def get_staging_data(
    session_id: str, 
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    from sqlalchemy import cast, String
    session_record = db.query(ImportSession).filter(ImportSession.id == session_id).first()
    query = db.query(CompanyImportStaging).filter(CompanyImportStaging.session_id == session_id)
    
    total = 0
    if status and status != 'all':
        if status == 'already_exists':
            query = query.filter(CompanyImportStaging.status == 'error', cast(CompanyImportStaging.errors, String).ilike("%already exists%"))
            total = query.count()
        elif status == 'warning':
            query = query.filter(CompanyImportStaging.status == 'valid', cast(CompanyImportStaging.warnings, String) != '[]', cast(CompanyImportStaging.warnings, String) != 'null')
            total = session_record.warning_count if session_record else query.count()
        elif status == 'valid':
            query = query.filter(CompanyImportStaging.status == 'valid', cast(CompanyImportStaging.warnings, String) == '[]')
            total = (session_record.valid_count - session_record.warning_count) if session_record else query.count()
        else:
            query = query.filter(CompanyImportStaging.status == status)
            if status == 'error' and session_record:
                total = session_record.error_count
            else:
                total = query.count()
    else:
        total = session_record.total_rows if session_record else query.count()

    items = query.order_by(CompanyImportStaging.row_number).offset((page - 1) * page_size).limit(page_size).all()
    
    results = []
    for item in items:
        clean_data = {
            "identifier": item.identifier,
            "company_name": item.company_name,
            "tax_number": item.tax_number,
            "email": item.email,
            "phone": item.phone,
            "address": item.address,
            "governorate": item.governorate,
            "postal_code": item.postal_code,
            "sector_id": item.sector_id,
            "activity_id": item.activity_id,
            "raw_sector": item.raw_sector,
            "raw_activity": item.raw_activity,
        }
        results.append({
            "row_number": item.row_number,
            "status": item.status,
            "errors": item.errors or [],
            "warnings": item.warnings or [],
            "data": clean_data
        })
        
    return {
        "total_rows": total,
        "page": page,
        "page_size": page_size,
        "rows": results
    }


@router.delete("/import/session/{session_id}")
def delete_import_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    session_record = db.query(ImportSession).filter(ImportSession.id == session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Delete associated staging rows first to avoid orphaned data
    db.query(CompanyImportStaging).filter(CompanyImportStaging.session_id == session_id).delete(synchronize_session=False)
    db.delete(session_record)
    db.commit()

    # Try to clean up the uploaded file
    file_path = os.path.join("uploads", f"import_{session_id}.xlsx")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to delete {file_path}: {e}")

    return {"status": "success", "message": "Import session cancelled."}

@router.patch("/import/staging/{session_id}/{row_number}")
def update_staging_row(
    session_id: str,
    row_number: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    row = db.query(CompanyImportStaging).filter(
        CompanyImportStaging.session_id == session_id,
        CompanyImportStaging.row_number == row_number
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Row not found.")

    # Apply field updates
    if "identifier" in data: row.identifier = data["identifier"]
    if "company_name" in data: row.company_name = data["company_name"]
    if "tax_number" in data: row.tax_number = data["tax_number"]
    if "email" in data: row.email = data["email"]
    if "phone" in data: row.phone = data["phone"]
    if "address" in data: row.address = data["address"]
    if "governorate" in data: row.governorate = data["governorate"]
    if "postal_code" in data: row.postal_code = data["postal_code"]
    if "sector_id" in data: row.sector_id = data["sector_id"]
    if "activity_id" in data: row.activity_id = data["activity_id"]

    # Re-run validation logic to ensure the row is actually valid
    errors = []
    if not row.identifier:
        errors.append("Identifier is required.")
    if not row.company_name:
        errors.append("Company name is required.")
    if not row.sector_id:
        errors.append("Sector is required.")
    if not row.activity_id:
        errors.append("Activity is required.")
    if row.email and not _validate_email(row.email):
        errors.append(f"Email '{row.email}' is not a valid email address.")
    if row.email and db.query(Company).filter(Company.email == row.email, Company.id != None).first():
        errors.append(f"Email '{row.email}' already exists in the database.")
    if row.identifier and db.query(Company).filter(Company.identifier == row.identifier).first():
        errors.append(f"Identifier '{row.identifier}' already exists in the database.")

    was_error = row.status == "error"
    if errors:
        row.status = "error"
        row.errors = errors
    else:
        row.status = "valid"
        row.errors = []
        # Update session counts if the row was previously an error
        if was_error:
            session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
            if session:
                session.error_count = max(0, session.error_count - 1)
                session.valid_count += 1

    db.commit()
    return {"status": "success", "is_valid": not errors, "errors": errors}

@router.post("/import/confirm", response_model=ImportConfirmResponse)
def confirm_import(
    payload: ImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieves the valid rows from the staging table for the given session
    and bulk-inserts them into the companies table in a single transaction.
    """
    session_record = db.query(ImportSession).filter(ImportSession.id == payload.session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found.")

    staging_rows = db.query(CompanyImportStaging).filter(
        CompanyImportStaging.session_id == payload.session_id,
        CompanyImportStaging.status == "valid"
    ).all()

    imported = 0
    skipped = 0
    errors: list[str] = []
    companies_to_add: list[Company] = []

    # Pre-fetch existing identifiers and emails for fast duplicate detection
    existing_identifiers = {str(c[0]).lower() for c in db.query(Company.identifier).all() if c[0]}
    existing_emails = {str(c[0]).lower() for c in db.query(Company.email).filter(Company.email.isnot(None)).all() if c[0]}

    for row in staging_rows:
        try:
            ident_lower = (row.identifier or "").lower()
            email_lower = (row.email or "").lower()

            if ident_lower in existing_identifiers:
                skipped += 1
                errors.append(f"Skipped '{row.identifier}': identifier already exists.")
                continue
            if email_lower and email_lower in existing_emails:
                skipped += 1
                errors.append(f"Skipped '{row.identifier}': email already exists.")
                continue

            companies_to_add.append(Company(
                identifier=row.identifier,
                company_name=row.company_name,
                tax_number=row.tax_number,
                email=row.email,
                phone=row.phone,
                address=row.address,
                governorate=row.governorate,
                postal_code=row.postal_code,
                sector_id=row.sector_id,
                activity_id=row.activity_id,
                status="ACTIVE",
            ))
            existing_identifiers.add(ident_lower)
            if email_lower:
                existing_emails.add(email_lower)
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Error processing '{row.identifier}': {str(e)}")

    # Single bulk insert then clean up staging data
    try:
        if companies_to_add:
            db.bulk_save_objects(companies_to_add)
        db.query(CompanyImportStaging).filter(
            CompanyImportStaging.session_id == payload.session_id
        ).delete(synchronize_session=False)
        db.delete(session_record)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed during database write: {str(e)}")

    return ImportConfirmResponse(imported=imported, skipped=skipped, errors=errors)
