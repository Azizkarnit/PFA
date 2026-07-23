# pyrefly: ignore [missing-import]
import datetime
from typing import Optional
from sqlalchemy import Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class CollectionTracking(Base):
    __tablename__ = "collection_tracking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    passage_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_passages.id"))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    status: Mapped[str] = mapped_column(
        Enum("NOT_STARTED", "IN_PROGRESS", "COMPLETED", name="collection_status_enum"), default="NOT_STARTED"
    )
    first_access_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
