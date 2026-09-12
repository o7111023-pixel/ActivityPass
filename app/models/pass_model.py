from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class MembershipPass(Base):
    __tablename__ = "membership_passes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"))
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    barcode_type: Mapped[str] = mapped_column(String(20), default="CODE128")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    visits_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activity = relationship("Activity", back_populates="passes")
    purchase = relationship("Purchase", back_populates="membership_pass", uselist=False)
