from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CheckIn(Base):
    __tablename__ = "checkins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_id: Mapped[int] = mapped_column(ForeignKey("membership_passes.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    result: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(255))
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
