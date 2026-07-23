# pyrefly: ignore [missing-import]
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SurveyQuestionnaire(Base):
    __tablename__ = "survey_questionnaires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    passage_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_passages.id"))
    questionnaire_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    questionnaire_pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "INACTIVE", "ARCHIVED", name="questionnaire_status_enum"), default="ACTIVE"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())

    passage: Mapped["SurveyPassage"] = relationship("SurveyPassage", back_populates="questionnaires")
