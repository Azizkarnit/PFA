# pyrefly: ignore [missing-import]
from typing import List
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name_fr: Mapped[str] = mapped_column(String(255))
    name_ar: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))

    companies: Mapped[List["Company"]] = relationship("Company", back_populates="sector")
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="sector")
