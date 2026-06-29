# pyrefly: ignore [missing-import]
import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class SurveyResultFile(Base):
    __tablename__ = "survey_result_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(Integer, ForeignKey("surveys.id"))
    sector_id: Mapped[int] = mapped_column(Integer, ForeignKey("sectors.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str] = mapped_column(Enum("PDF", "EXCEL", name="file_type_enum"))
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
