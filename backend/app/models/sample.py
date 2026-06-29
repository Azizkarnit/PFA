# pyrefly: ignore [missing-import]
import datetime
from typing import List
from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    passage_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_passages.id"))
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    total_companies: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    passage: Mapped["SurveyPassage"] = relationship("SurveyPassage", back_populates="samples")
    companies: Mapped[List["SampleCompany"]] = relationship("SampleCompany", back_populates="sample")
