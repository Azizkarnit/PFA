import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AppNotification(Base):
    __tablename__ = "app_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    
    # Can be INFO, WARNING, SUCCESS, ERROR
    type: Mapped[str] = mapped_column(String(50), default="INFO")
    
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    
    user = relationship("User")
