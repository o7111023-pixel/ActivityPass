from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.rewards import (
    DAILY_REWARD_STEP,
    WELCOME_REWARD,
    claim_daily_reward,
    get_balance,
    grant_welcome_reward,
)
try:
    from app.security import hash_password, verify_password
except ModuleNotFoundError as exc:
    if exc.name == "jose":
        hash_password = verify_password = None
    else:
        raise


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def make_user(db):
    password_hash = hash_password("password123") if hash_password else "test-salt:test-digest"
    user = User(email="test@example.com", full_name="Test User", password_hash=password_hash)
    db.add(user)
    db.commit()
    return user


def add_daily(db, user_id, when, amount):
    balance = get_balance(db, user_id) + amount
    db.add(WalletTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=balance,
        transaction_type="DAILY_REWARD",
        description="test daily reward",
        reference=when.isoformat(),
        created_at=datetime.combine(when, datetime.min.time()),
    ))
    db.commit()


def test_welcome_reward_is_exactly_once():
    db = make_db()
    user = make_user(db)
    assert grant_welcome_reward(db, user.id) == WELCOME_REWARD
    assert grant_welcome_reward(db, user.id) == WELCOME_REWARD
    rows = db.query(WalletTransaction).filter_by(user_id=user.id, transaction_type="WELCOME_REWARD").all()
    assert len(rows) == 1


def test_registration_day_does_not_also_get_daily_reward():
    db = make_db()
    user = make_user(db)
    grant_welcome_reward(db, user.id)
    claimed, balance, streak = claim_daily_reward(db, user.id)
    assert claimed is False
    assert balance == WELCOME_REWARD
    assert streak == 0


def test_first_daily_reward_is_700_and_cannot_be_multiplied_by_refresh():
    db = make_db()
    user = make_user(db)
    welcome = WalletTransaction(
        user_id=user.id,
        amount=WELCOME_REWARD,
        balance_after=WELCOME_REWARD,
        transaction_type="WELCOME_REWARD",
        description="old welcome",
        reference="WELCOME",
        created_at=datetime.combine(date.today() - timedelta(days=1), datetime.min.time()),
    )
    db.add(welcome)
    db.commit()

    claimed, balance, streak = claim_daily_reward(db, user.id)
    assert claimed is True
    assert balance == WELCOME_REWARD + DAILY_REWARD_STEP
    assert streak == 1

    claimed2, balance2, streak2 = claim_daily_reward(db, user.id)
    assert claimed2 is False
    assert balance2 == balance
    assert streak2 == 1


def test_consecutive_streak_grows_by_700_per_day():
    db = make_db()
    user = make_user(db)
    yesterday = date.today() - timedelta(days=1)
    add_daily(db, user.id, yesterday, 700)
    claimed, balance, streak = claim_daily_reward(db, user.id)
    assert claimed is True
    assert streak == 2
    assert balance == 700 + 1400


def test_missing_day_resets_streak_to_one():
    db = make_db()
    user = make_user(db)
    two_days_ago = date.today() - timedelta(days=2)
    add_daily(db, user.id, two_days_ago, 700)
    claimed, balance, streak = claim_daily_reward(db, user.id)
    assert claimed is True
    assert streak == 1
    assert balance == 700 + 700


def test_password_hash_is_not_plaintext_and_verifies():
    if hash_password is None:
        import pytest
        pytest.skip("python-jose is not installed in the current execution environment")
    password = "strong-password-123"
    stored = hash_password(password)
    assert password not in stored
    assert verify_password(password, stored) is True
    assert verify_password("wrong-password", stored) is False
