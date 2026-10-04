import random

from sqlalchemy.orm import Session

from app.models.wallet import WalletTransaction


# ============================================================
# UNLOCK REQUIREMENTS
# ============================================================

SAFE_UNLOCK_BALANCE = 30_000
RISK_UNLOCK_BALANCE = 100_000
HIGH_ROLLER_UNLOCK_BALANCE = 500_000


# ============================================================
# BET LIMITS
# ============================================================

SAFE_MAX_BET = 5_000
RISK_MAX_BET = 50_000


# ============================================================
# SAFE WHEEL
#
# Bets:
# 500 - 5,000 AP
#
# 12 sectors
# ============================================================

SAFE_WHEEL_SEGMENTS = [
    {
        "sector": 0,
        "multiplier": 0.0,
        "fixed_win": 0,
        "weight": 25.00,
    },
    {
        "sector": 1,
        "multiplier": 0.25,
        "fixed_win": None,
        "weight": 12.00,
    },
    {
        "sector": 2,
        "multiplier": 0.5,
        "fixed_win": None,
        "weight": 11.00,
    },
    {
        "sector": 3,
        "multiplier": 0.75,
        "fixed_win": None,
        "weight": 10.00,
    },
    {
        "sector": 4,
        "multiplier": 1.0,
        "fixed_win": None,
        "weight": 9.00,
    },
    {
        "sector": 5,
        "multiplier": 1.25,
        "fixed_win": None,
        "weight": 7.00,
    },
    {
        "sector": 6,
        "multiplier": 0.0,
        "fixed_win": 2_000,
        "weight": 6.00,
    },
    {
        "sector": 7,
        "multiplier": 1.5,
        "fixed_win": None,
        "weight": 6.00,
    },
    {
        "sector": 8,
        "multiplier": 0.0,
        "fixed_win": 4_000,
        "weight": 5.00,
    },
    {
        "sector": 9,
        "multiplier": 2.0,
        "fixed_win": None,
        "weight": 4.00,
    },
    {
        "sector": 10,
        "multiplier": 3.0,
        "fixed_win": None,
        "weight": 4.99,
    },
    {
        "sector": 11,
        "multiplier": 0.0,
        "fixed_win": 222_000,
        "weight": 0.01,
    },
]


# ============================================================
# RISK WHEEL
#
# Bets:
# 7,500 - 50,000 AP
#
# 12 sectors
# ============================================================

RISK_WHEEL_SEGMENTS = [
    {
        "sector": 0,
        "multiplier": 0.0,
        "fixed_win": 0,
        "weight": 25.00,
    },
    {
        "sector": 1,
        "multiplier": 0.25,
        "fixed_win": None,
        "weight": 10.00,
    },
    {
        "sector": 2,
        "multiplier": 0.75,
        "fixed_win": None,
        "weight": 10.00,
    },
    {
        "sector": 3,
        "multiplier": 1.0,
        "fixed_win": None,
        "weight": 10.00,
    },
    {
        "sector": 4,
        "multiplier": 1.25,
        "fixed_win": None,
        "weight": 8.00,
    },
    {
        "sector": 5,
        "multiplier": 1.5,
        "fixed_win": None,
        "weight": 7.00,
    },
    {
        "sector": 6,
        "multiplier": 0.0,
        "fixed_win": 10_000,
        "weight": 7.00,
    },
    {
        "sector": 7,
        "multiplier": 2.0,
        "fixed_win": None,
        "weight": 6.00,
    },
    {
        "sector": 8,
        "multiplier": 0.0,
        "fixed_win": 20_000,
        "weight": 5.00,
    },
    {
        "sector": 9,
        "multiplier": 2.5,
        "fixed_win": None,
        "weight": 5.00,
    },
    {
        "sector": 10,
        "multiplier": 5.0,
        "fixed_win": None,
        "weight": 6.99,
    },
    {
        "sector": 11,
        "multiplier": 0.0,
        "fixed_win": 555_000,
        "weight": 0.01,
    },
]


# ============================================================
# HIGH ROLLER
#
# Bets:
# 70,000 - 100,000 AP
#
# 12 sectors
#
# 0x DOES NOT EXIST HERE.
# Minimum result = 0.25x
#
# Ultra jackpots:
# +222K = 0.01%
# +444K = 0.01%
# +999K = 0.01%
# ============================================================

HIGH_ROLLER_SEGMENTS = [
    {
        "sector": 0,
        "multiplier": 0.25,
        "fixed_win": None,
        "weight": 25.00,
    },
    {
        "sector": 1,
        "multiplier": 0.5,
        "fixed_win": None,
        "weight": 17.00,
    },
    {
        "sector": 2,
        "multiplier": 0.75,
        "fixed_win": None,
        "weight": 12.00,
    },
    {
        "sector": 3,
        "multiplier": 1.0,
        "fixed_win": None,
        "weight": 10.00,
    },
    {
        "sector": 4,
        "multiplier": 1.5,
        "fixed_win": None,
        "weight": 8.00,
    },
    {
        "sector": 5,
        "multiplier": 2.0,
        "fixed_win": None,
        "weight": 7.00,
    },
    {
        "sector": 6,
        "multiplier": 0.0,
        "fixed_win": 222_000,
        "weight": 0.01,
    },
    {
        "sector": 7,
        "multiplier": 0.0,
        "fixed_win": 444_000,
        "weight": 0.01,
    },
    {
        "sector": 8,
        "multiplier": 5.0,
        "fixed_win": None,
        "weight": 7.00,
    },
    {
        "sector": 9,
        "multiplier": 7.5,
        "fixed_win": None,
        "weight": 5.00,
    },
    {
        "sector": 10,
        "multiplier": 10.0,
        "fixed_win": None,
        "weight": 8.97,
    },
    {
        "sector": 11,
        "multiplier": 0.0,
        "fixed_win": 999_000,
        "weight": 0.01,
    },
]


# ============================================================
# WHEEL LEVEL
# ============================================================

def get_wheel_level(bet_amount: int) -> str:
    """
    Determine wheel level based on bet amount.
    """

    if bet_amount <= SAFE_MAX_BET:
        return "SAFE"

    if bet_amount <= RISK_MAX_BET:
        return "RISK"

    return "HIGH_ROLLER"


# ============================================================
# WHEEL SEGMENTS
# ============================================================

def get_wheel_segments(bet_amount: int) -> list[dict]:
    """
    Return the correct wheel configuration
    for the selected bet.
    """

    level = get_wheel_level(bet_amount)

    if level == "SAFE":
        return SAFE_WHEEL_SEGMENTS

    if level == "RISK":
        return RISK_WHEEL_SEGMENTS

    return HIGH_ROLLER_SEGMENTS


# ============================================================
# HIGHEST BALANCE
# ============================================================

def get_highest_balance(db: Session, user_id: int) -> int:
    """
    Find the highest balance the user has ever reached.
    """

    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == user_id)
        .order_by(WalletTransaction.balance_after.desc())
        .first()
    )

    return transaction.balance_after if transaction else 0


# ============================================================
# UNLOCK CHECKS
# ============================================================

def is_fortune_wheel_unlocked(
    db: Session,
    user_id: int,
) -> bool:
    """
    SAFE wheel unlock.
    """

    return (
        get_highest_balance(db, user_id)
        >= SAFE_UNLOCK_BALANCE
    )


def is_risk_wheel_unlocked(
    db: Session,
    user_id: int,
) -> bool:
    """
    RISK wheel unlock.
    """

    return (
        get_highest_balance(db, user_id)
        >= RISK_UNLOCK_BALANCE
    )


def is_high_roller_unlocked(
    db: Session,
    user_id: int,
) -> bool:
    """
    HIGH ROLLER wheel unlock.
    """

    return (
        get_highest_balance(db, user_id)
        >= HIGH_ROLLER_UNLOCK_BALANCE
    )


# ============================================================
# SPIN
# ============================================================

def spin_wheel(bet_amount: int) -> dict:
    """
    Select a random sector according to its weight.
    """

    segments = get_wheel_segments(bet_amount)

    return random.choices(
        segments,
        weights=[
            segment["weight"]
            for segment in segments
        ],
        k=1,
    )[0]


# ============================================================
# CALCULATE WIN
# ============================================================

def calculate_win(
    bet_amount: int,
    multiplier: float,
    fixed_win: int | None = None,
) -> int:
    """
    Calculate the payout.

    Fixed prizes return the exact fixed amount.
    Multiplier prizes return bet * multiplier.
    """

    if fixed_win is not None:
        return fixed_win

    return int(bet_amount * multiplier)
