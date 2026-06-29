# pyrefly: ignore [missing-import]
import datetime
from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleCompany(Base):
    __tablename__ = "sample_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(Integer, ForeignKey("samples.id"))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    sample: Mapped["Sample"] = relationship("Sample", back_populates="companies")
