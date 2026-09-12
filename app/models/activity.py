from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    schedule_days: Mapped[str] = mapped_column(String(100), default="")
    start_time: Mapped[str] = mapped_column(String(10), default="09:00")
    end_time: Mapped[str] = mapped_column(String(10), default="18:00")
    max_visits: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider = relationship("Provider", back_populates="activities")
    passes = relationship("MembershipPass", back_populates="activity")
    favorites = relationship("Favorite", back_populates="activity", cascade="all, delete-orphan")
