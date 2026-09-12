from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ActivityView(Base):
    __tablename__ = "activity_views"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_id", "view_date", name="uq_activity_view_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    view_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
