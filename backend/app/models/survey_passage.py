# pyrefly: ignore [missing-import]
import datetime
from typing import Optional, List
from sqlalchemy import Integer, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SurveyPassage(Base):
    __tablename__ = "survey_passages"
    __table_args__ = (
        UniqueConstraint("survey_id", "year", "passage_number", name="uq_survey_year_passage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(Integer, ForeignKey("surveys.id"))
    year: Mapped[int] = mapped_column(Integer)
    passage_number: Mapped[int] = mapped_column(Integer)
    opening_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    closing_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        Enum("DRAFT", "READY", "OPEN", "CLOSED", "ARCHIVED", name="passage_status_enum"), default="DRAFT"
    )
    activated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    activated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    survey: Mapped["Survey"] = relationship("Survey", back_populates="passages")
    questionnaires: Mapped[List["SurveyQuestionnaire"]] = relationship("SurveyQuestionnaire", back_populates="passage")
    samples: Mapped[List["Sample"]] = relationship("Sample", back_populates="passage")
