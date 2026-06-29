import datetime
from typing import Optional
from sqlalchemy import Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class SurveyActivation(Base):
    __tablename__ = "survey_activations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    passage_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_passages.id"))
    activated_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    activated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
