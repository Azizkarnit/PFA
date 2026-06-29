# pyrefly: ignore [missing-import]
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    channel: Mapped[str] = mapped_column(Enum("EMAIL", name="notification_channel_enum"), default="EMAIL")
    type: Mapped[str] = mapped_column(
        Enum("OTP", "ACTIVATION", "INVITATION", "REMINDER", "RESET_PASSWORD", name="notification_type_enum")
    )
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(Enum("PENDING", "SENT", "FAILED", name="notification_status_enum"), default="PENDING")
    provider_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
