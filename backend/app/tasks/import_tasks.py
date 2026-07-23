import os
import io
import openpyxl
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.sector import Sector
from app.models.activity import Activity
from app.models.import_session import ImportSession, CompanyImportStaging
import re
import logging

logger = logging.getLogger(__name__)
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
    if cleaned.lower() in ["null", "n/a", "none", "nan", "-", "undefined"]:
        return ""
    return cleaned

@celery_app.task
def process_excel_import(session_id: str, file_path: str):
    db: Session = SessionLocal()
    try:
        session_record = db.query(ImportSession).filter(ImportSession.id == session_id).first()
        if not session_record:
            return

        # Load file
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
        except Exception as e:
            session_record.status = "failed"
            session_record.error_message = f"Could not read the Excel file: {str(e)}"
            db.commit()
            return

        if ws is None:
            session_record.status = "failed"
            session_record.error_message = "The Excel file has no active sheet."
            db.commit()
            return

        rows_iter = list(ws.iter_rows(values_only=True))
        try:
            wb.close()
        except Exception as e:
            logger.warning(f"Error closing workbook for session {session_id}: {e}")

        if not rows_iter:
            session_record.status = "failed"
            session_record.error_message = "The file is empty."
            db.commit()
            return

        header_row = [_clean(h).lower() for h in rows_iter[0]]
        col_map = {}
        missing_columns = []
        for col_name in EXPECTED_COLUMNS:
            try:
                col_map[col_name] = header_row.index(col_name)
            except ValueError:
                missing_columns.append(col_name)
                
        if missing_columns:
            session_record.status = "failed"
            session_record.error_message = f"Invalid file template. Missing required columns: {', '.join(missing_columns)}"
            db.commit()
            return

        data_rows = rows_iter[1:]

        # DB Pre-loads
        sectors_by_name = {s.name.strip().lower(): s for s in db.query(Sector).all()}
        activities_by_name = {a.name.strip().lower(): a for a in db.query(Activity).all()}
        existing_identifiers = {str(c[0]).strip().lower() for c in db.query(Company.identifier).all() if c[0]}
        existing_emails = {str(c[0]).strip().lower() for c in db.query(Company.email).filter(Company.email.isnot(None)).all() if c[0]}

        seen_identifiers_in_file: set[str] = set()
        seen_emails_in_file: set[str] = set()

        valid_count = 0
        error_count = 0
        warning_count = 0
        total_rows = 0

        staging_records = []

        def get_col(row_vals, col_name):
            idx = col_map.get(col_name)
            if idx is None or idx >= len(row_vals):
                return ""
            return _clean(row_vals[idx])

        for i, row_vals in enumerate(data_rows, start=2):
            identifier   = get_col(row_vals, "identifier")
            company_name = get_col(row_vals, "company_name")
            tax_number   = get_col(row_vals, "tax_number") or None
            email        = get_col(row_vals, "email") or None
            phone        = get_col(row_vals, "phone") or None
            address      = get_col(row_vals, "address") or None
            governorate  = get_col(row_vals, "governorate") or None
            postal_code  = get_col(row_vals, "postal_code") or None
            sector_name  = get_col(row_vals, "sector")
            activity_name= get_col(row_vals, "activity")

            all_values = [identifier, company_name, tax_number or "", email or "",
                          phone or "", address or "", governorate or "", postal_code or "",
                          sector_name, activity_name]
            if not any(v.strip() for v in all_values):
                continue
                
            total_rows += 1
            errors = []
            warnings = []

            # Validations
            if not identifier:
                errors.append("Identifier is required.")
            elif len(identifier) > 100:
                errors.append(f"Identifier is too long ({len(identifier)} chars, max 100).")

            if not company_name:
                errors.append("Company name is required.")
            elif len(company_name) > 255:
                errors.append(f"Company name is too long ({len(company_name)} chars, max 255).")

            sector_obj = sectors_by_name.get(sector_name.lower()) if sector_name else None
            activity_obj = activities_by_name.get(activity_name.lower()) if activity_name else None

            if not sector_name:
                errors.append("Sector is required.")
            elif not sector_obj:
                errors.append(f"Sector '{sector_name}' not found in the database.")

            if not activity_name:
                errors.append("Activity is required.")
            elif not activity_obj:
                errors.append(f"Activity '{activity_name}' not found in the database.")

            if email:
                email_lower = email.lower()
                if len(email) > 255:
                    errors.append(f"Email is too long ({len(email)} chars, max 255).")
                elif not _validate_email(email):
                    errors.append(f"Email '{email}' is not a valid email address.")
                elif email_lower in existing_emails:
                    errors.append(f"Email '{email}' already exists in the database.")
                elif email_lower in seen_emails_in_file:
                    errors.append(f"Email '{email}' appears more than once in this file.")
                else:
                    seen_emails_in_file.add(email_lower)

            if identifier and len(identifier) <= 100:
                ident_lower = identifier.lower()
                if ident_lower in existing_identifiers:
                    errors.append(f"Identifier '{identifier}' already exists in the database.")
                elif ident_lower in seen_identifiers_in_file:
                    errors.append(f"Identifier '{identifier}' appears more than once in this file.")
                else:
                    seen_identifiers_in_file.add(ident_lower)

            if phone and len(phone) > 30:
                warnings.append(f"Phone number is too long ({len(phone)} chars, max 30) — will be truncated.")
                phone = phone[:30]

            if errors:
                row_status = "error"
                error_count += 1
            else:
                row_status = "valid"
                valid_count += 1
                if warnings:
                    warning_count += 1

            staging_records.append(CompanyImportStaging(
                session_id=session_id,
                row_number=i,
                status=row_status,
                errors=errors if errors else [],
                warnings=warnings if warnings else [],
                identifier=identifier,
                company_name=company_name,
                tax_number=tax_number,
                email=email,
                phone=phone,
                address=address,
                governorate=governorate,
                postal_code=postal_code,
                sector_id=sector_obj.id if sector_obj else None,
                activity_id=activity_obj.id if activity_obj else None,
                raw_sector=sector_name,
                raw_activity=activity_name
            ))

            # Batch insert to avoid huge memory usage
            if len(staging_records) >= 2000:
                db.bulk_save_objects(staging_records)
                db.commit()
                staging_records = []

        if staging_records:
            db.bulk_save_objects(staging_records)
            db.commit()

        session_record.total_rows = total_rows
        session_record.valid_count = valid_count
        session_record.error_count = error_count
        session_record.warning_count = warning_count
        session_record.status = "completed"
        db.commit()
        
    except Exception as e:
        session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
        if session:
            session.status = "failed"
            session.error_message = f"An unexpected error occurred: {str(e)}"
            db.commit()
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        db.close()
