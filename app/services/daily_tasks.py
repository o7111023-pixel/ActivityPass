from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session

from app.models.activity_view import ActivityView
from app.models.favorite import Favorite
from app.models.focus_session import FocusSession
from app.models.purchase import Purchase
from app.models.wallet import WalletTransaction


TASKS = [
    {
        "key": "explore_3",
        "title": "Explore 3 activities",
        "description": "Open three different experiences in Explore today.",
        "reward": 700,
        "kind": "explore",
        "target": 3,
    },
    {
        "key": "favorite_2",
        "title": "Save 2 favourites",
        "description": "Like two activities you would try later.",
        "reward": 500,
        "kind": "favorite",
        "target": 2,
    },
    {
        "key": "buy_4000",
        "title": "Spend 4,000 AP",
        "description": "Purchase one membership worth at least 4,000 AP.",
        "reward": 1200,
        "kind": "purchase",
        "target": 4000,
    },
    {
        "key": "focus_20",
        "title": "Complete a 20-minute session",
        "description": "Start a virtual activity session and stay with it for 20 minutes.",
        "reward": 900,
        "kind": "focus",
        "target": 20,
    },
    {
        "key": "explore_5",
        "title": "Explore 5 categories",
        "description": "Open five different activities from Explore today.",
        "reward": 1100,
        "kind": "explore",
        "target": 5,
    },
    {
        "key": "favorite_3",
        "title": "Build a shortlist",
        "description": "Save three activities to your favourites.",
        "reward": 800,
        "kind": "favorite",
        "target": 3,
    },
]


def today_bounds():
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    return start, end


def todays_tasks():
    # Rotate the daily set without needing a cron job or a database table.
    day = date.today().toordinal()
    offset = day % len(TASKS)
    rotated = TASKS[offset:] + TASKS[:offset]
    return rotated[:3]


def _claimed(db: Session, user_id: int, key: str) -> bool:
    ref = f"TASK:{date.today().isoformat()}:{key}"
    return db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id,
        WalletTransaction.transaction_type == "TASK_REWARD",
        WalletTransaction.reference == ref,
    ).first() is not None


def _progress(db: Session, user_id: int, task: dict) -> int:
    start, end = today_bounds()
    kind = task["kind"]

    if kind == "explore":
        return db.query(ActivityView).filter(
            ActivityView.user_id == user_id,
            ActivityView.view_date == date.today(),
        ).count()

    if kind == "favorite":
        return db.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.created_at >= start,
            Favorite.created_at < end,
        ).count()

    if kind == "purchase":
        return 1 if db.query(Purchase).filter(
            Purchase.user_id == user_id,
            Purchase.amount >= task["target"],
            Purchase.created_at >= start,
            Purchase.created_at < end,
        ).first() else 0

    if kind == "focus":
        session = db.query(FocusSession).filter(
            FocusSession.user_id == user_id,
            FocusSession.started_at >= start,
            FocusSession.started_at < end,
        ).order_by(FocusSession.id.desc()).first()
        if not session:
            return 0
        if session.completed_at:
            return task["target"]
        elapsed = max(0, int((datetime.utcnow() - session.started_at).total_seconds() // 60))
        return min(task["target"], elapsed)

    return 0


def get_task_state(db: Session, user_id: int):
    result = []
    for task in todays_tasks():
        progress = _progress(db, user_id, task)
        target = task["target"]
        claimed = _claimed(db, user_id, task["key"])
        result.append({
            **task,
            "progress": min(progress, target),
            "completed": progress >= target,
            "claimed": claimed,
        })
    return result


def claim_task(db: Session, user_id: int, key: str):
    task = next((x for x in todays_tasks() if x["key"] == key), None)
    if not task:
        return False, "Task is not active today."
    if _claimed(db, user_id, key):
        return False, "Task reward already claimed."
    if _progress(db, user_id, task) < task["target"]:
        return False, "Complete the task first."

    balance_row = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id
    ).order_by(WalletTransaction.id.desc()).first()
    balance = balance_row.balance_after if balance_row else 0
    new_balance = balance + task["reward"]
    ref = f"TASK:{date.today().isoformat()}:{task['key']}"
    db.add(WalletTransaction(
        user_id=user_id,
        amount=task["reward"],
        balance_after=new_balance,
        transaction_type="TASK_REWARD",
        description=f"Daily task: {task['title']}",
        reference=ref,
    ))
    db.commit()
    return True, new_balance


def start_focus_session(db: Session, user_id: int):
    start, end = today_bounds()
    current = db.query(FocusSession).filter(
        FocusSession.user_id == user_id,
        FocusSession.started_at >= start,
        FocusSession.started_at < end,
        FocusSession.completed_at.is_(None),
    ).order_by(FocusSession.id.desc()).first()
    if current:
        return current
    current = FocusSession(user_id=user_id)
    db.add(current)
    db.commit()
    db.refresh(current)
    return current


def weekly_challenge_state(db: Session, user_id: int):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    start = datetime.combine(week_start, time.min)
    end = start + timedelta(days=7)
    view_count = db.query(ActivityView.activity_id).filter(
        ActivityView.user_id == user_id,
        ActivityView.view_date >= week_start,
        ActivityView.view_date < end.date(),
    ).distinct().count()
    purchase_count = db.query(Purchase.activity_id).filter(
        Purchase.user_id == user_id,
        Purchase.created_at >= start,
        Purchase.created_at < end,
    ).distinct().count()
    count = max(view_count, purchase_count)
    ref = f"WEEKLY:{today.isocalendar().year}-W{today.isocalendar().week}"
    claimed = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id,
        WalletTransaction.transaction_type == "WEEKLY_REWARD",
        WalletTransaction.reference == ref,
    ).first() is not None
    return {"count": min(count, 3), "target": 3, "reward": 4000, "completed": count >= 3, "claimed": claimed}


def claim_weekly_challenge(db: Session, user_id: int):
    state = weekly_challenge_state(db, user_id)
    if not state["completed"]:
        return False, "Complete 3 different activities this week first."
    if state["claimed"]:
        return False, "Weekly reward already claimed."
    balance_row = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user_id
    ).order_by(WalletTransaction.id.desc()).first()
    balance = balance_row.balance_after if balance_row else 0
    new_balance = balance + state["reward"]
    today = date.today()
    ref = f"WEEKLY:{today.isocalendar().year}-W{today.isocalendar().week}"
    db.add(WalletTransaction(
        user_id=user_id,
        amount=state["reward"],
        balance_after=new_balance,
        transaction_type="WEEKLY_REWARD",
        description="Weekly challenge · 3 different activities",
        reference=ref,
    ))
    db.commit()
    return True, new_balance
