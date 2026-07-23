# pyrefly: ignore [missing-import]
from typing import List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sector_id: Mapped[int] = mapped_column(Integer, ForeignKey("sectors.id"))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))

    sector: Mapped["Sector"] = relationship("Sector", back_populates="activities")
    companies: Mapped[List["Company"]] = relationship("Company", back_populates="activity")
