# pyrefly: ignore [missing-import]
import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "LOCKED", "DISABLED", name="user_status_enum"), default="ACTIVE")
    first_login: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(Enum("ar", "fr", "en", name="language_enum"), default="fr")
    password_only_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(), onupdate=lambda: datetime.datetime.now()
    )

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="user", uselist=False)
    created_surveys: Mapped[List["Survey"]] = relationship("Survey", back_populates="creator")
    survey_assignments: Mapped[List["SurveyAssignment"]] = relationship("SurveyAssignment", back_populates="user")
