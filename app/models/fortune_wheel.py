from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FortuneWheelSpin(Base):
    __tablename__ = "fortune_wheel_spins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    bet_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    multiplier: Mapped[float] = mapped_column(
        nullable=False,
    )

    win_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
