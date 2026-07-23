# pyrefly: ignore [missing-import]
import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class QuestionnaireToken(Base):
    __tablename__ = "questionnaire_tokens"
    __table_args__ = (
        UniqueConstraint("contact_id", "passage_id", name="uq_contact_passage_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    passage_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_passages.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())

    contact: Mapped["Contact"] = relationship("Contact")
    company: Mapped["Company"] = relationship("Company")
    passage: Mapped["SurveyPassage"] = relationship("SurveyPassage")
