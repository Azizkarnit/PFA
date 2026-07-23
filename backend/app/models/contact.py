# pyrefly: ignore [missing-import]
import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "INACTIVE", name="contact_status_enum"), default="ACTIVE")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(), onupdate=lambda: datetime.datetime.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="contact")
    company: Mapped["Company"] = relationship("Company", back_populates="contacts")
