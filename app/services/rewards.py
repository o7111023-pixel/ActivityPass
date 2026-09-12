from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.wallet import WalletTransaction

DAILY_REWARD_STEP = 700
WELCOME_REWARD = 7500


def get_balance(db: Session, user_id: int) -> int:
    row = (db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == user_id)
        .order_by(WalletTransaction.id.desc()).first())
    return row.balance_after if row else 0


def grant_welcome_reward(db: Session, user_id: int) -> int:
    exists = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id,
        WalletTransaction.transaction_type == "WELCOME_REWARD"
    ).first()
    if exists:
        return get_balance(db, user_id)
    balance = get_balance(db, user_id) + WELCOME_REWARD
    db.add(WalletTransaction(user_id=user_id, amount=WELCOME_REWARD,
        balance_after=balance, transaction_type="WELCOME_REWARD",
        description="Welcome bonus for registration", reference="WELCOME"))
    db.commit()
    return balance


def _daily_dates(db: Session, user_id: int):
    rows = (db.query(WalletTransaction.reference)
        .filter(WalletTransaction.user_id == user_id,
                WalletTransaction.transaction_type == "DAILY_REWARD")
        .all())
    return {r[0] for r in rows if r[0]}


def get_streak(db: Session, user_id: int) -> int:
    """Return the active consecutive streak, including an unclaimed today.

    Before today's reward is claimed, yesterday's streak is still the streak
    the next claim should extend. After today's reward exists, counting starts
    from today.
    """
    dates = _daily_dates(db, user_id)
    today = date.today()
    cursor = today if today.isoformat() in dates else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_recent_checkins(db: Session, user_id: int, days: int = 28):
    dates = _daily_dates(db, user_id)
    today = date.today()
    return [
        {"date": today - timedelta(days=offset),
         "active": (today - timedelta(days=offset)).isoformat() in dates}
        for offset in range(days - 1, -1, -1)
    ]


def claim_daily_reward(db: Session, user_id: int):
    today = date.today().isoformat()
    welcome = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id,
        WalletTransaction.transaction_type == "WELCOME_REWARD"
    ).first()
    if welcome and welcome.created_at.date().isoformat() == today:
        return False, get_balance(db, user_id), 0

    exists = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id,
        WalletTransaction.transaction_type == "DAILY_REWARD",
        WalletTransaction.reference == today
    ).first()
    if exists:
        return False, get_balance(db, user_id), get_streak(db, user_id)

    # No cap: every consecutive active day makes the next reward larger.
    streak = get_streak(db, user_id) + 1
    amount = DAILY_REWARD_STEP * streak
    balance = get_balance(db, user_id) + amount
    db.add(WalletTransaction(user_id=user_id, amount=amount,
        balance_after=balance, transaction_type="DAILY_REWARD",
        description=f"Daily reward · Day {streak} streak",
        reference=today))
    db.commit()
    return True, balance, streak


def spend(db: Session, user_id: int, amount: int, description: str, reference: str):
    balance = get_balance(db, user_id)
    if amount > balance:
        raise ValueError("Not enough virtual credits")
    new_balance = balance - amount
    db.add(WalletTransaction(user_id=user_id, amount=-amount,
        balance_after=new_balance, transaction_type="PURCHASE",
        description=description, reference=reference))
    return new_balance
