import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    tax_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sector_id: Mapped[int] = mapped_column(Integer, ForeignKey("sectors.id"))
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"))
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    governorate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "INACTIVE", name="company_status_enum"), default="ACTIVE")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(), onupdate=lambda: datetime.datetime.now()
    )

    sector: Mapped["Sector"] = relationship("Sector", back_populates="companies")
    activity: Mapped["Activity"] = relationship("Activity", back_populates="companies")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company")
