from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hobbies: Mapped[str] = mapped_column(Text, default="")
    preferred_time: Mapped[str] = mapped_column(String(30), default="Evening")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    wallet = relationship("WalletTransaction", back_populates="user")
    virtual_card = relationship("VirtualCard", back_populates="user", uselist=False)
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
