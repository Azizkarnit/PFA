# pyrefly: ignore [missing-import]
import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User")
    action: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
