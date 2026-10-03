import random

from sqlalchemy.orm import Session

from app.models.wallet import WalletTransaction


FORTUNE_WHEEL_UNLOCK_BALANCE = 30_000


FORTUNE_WHEEL_SEGMENTS = [
    {"multiplier": 0.0, "weight": 25},
    {"multiplier": 0.1, "weight": 10},
    {"multiplier": 0.5, "weight": 15},
    {"multiplier": 1.0, "weight": 12},
    {"multiplier": 1.0, "weight": 12},
    {"multiplier": 1.5, "weight": 8},
    {"multiplier": 2.0, "weight": 7},
    {"multiplier": 2.0, "weight": 7},
    {"multiplier": 3.0, "weight": 4},
]


def get_highest_balance(db: Session, user_id: int) -> int:
    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == user_id)
        .order_by(WalletTransaction.balance_after.desc())
        .first()
    )

    return transaction.balance_after if transaction else 0


def is_fortune_wheel_unlocked(
    db: Session,
    user_id: int,
) -> bool:
    return (
        get_highest_balance(db, user_id)
        >= FORTUNE_WHEEL_UNLOCK_BALANCE
    )


def spin_wheel() -> float:
    """
    Select one of the 9 wheel sectors.

    The two 1x and two 2x sectors are separate
    physical sectors but have the same multiplier.
    """

    selected_segment = random.choices(
        FORTUNE_WHEEL_SEGMENTS,
        weights=[
            segment["weight"]
            for segment in FORTUNE_WHEEL_SEGMENTS
        ],
        k=1,
    )[0]

    return selected_segment["multiplier"]


def calculate_win(
    bet_amount: int,
    multiplier: float,
) -> int:
    return int(bet_amount * multiplier)
