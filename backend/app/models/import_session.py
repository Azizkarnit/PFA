import datetime
import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Text, Enum, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(20), default="processing") # processing, completed, failed
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    
    staging_rows: Mapped[List["CompanyImportStaging"]] = relationship("CompanyImportStaging", back_populates="session", cascade="all, delete-orphan")


class CompanyImportStaging(Base):
    __tablename__ = "company_import_staging"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_sessions.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))  # valid, error, warning
    
    # Validation info stored as JSON arrays of strings
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Raw extracted data (using same types as Company model)
    identifier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    governorate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    sector_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    activity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    raw_sector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_activity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    session: Mapped["ImportSession"] = relationship("ImportSession", back_populates="staging_rows")
