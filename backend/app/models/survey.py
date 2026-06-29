# pyrefly: ignore [missing-import]
import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    periodicity_id: Mapped[int] = mapped_column(Integer, ForeignKey("periodicities.id"))
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "INACTIVE", "ARCHIVED", name="survey_status_enum"), default="ACTIVE")
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    creator: Mapped["User"] = relationship("User", back_populates="created_surveys")
    assignments: Mapped[List["SurveyAssignment"]] = relationship("SurveyAssignment", back_populates="survey")
    passages: Mapped[List["SurveyPassage"]] = relationship("SurveyPassage", back_populates="survey")
