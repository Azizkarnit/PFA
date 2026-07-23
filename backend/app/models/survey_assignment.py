# pyrefly: ignore [missing-import]
import datetime
from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SurveyAssignment(Base):
    __tablename__ = "survey_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(Integer, ForeignKey("surveys.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    assigned_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())

    survey: Mapped["Survey"] = relationship("Survey", back_populates="assignments")
    user: Mapped["User"] = relationship("User", back_populates="survey_assignments")
