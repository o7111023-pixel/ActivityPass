from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.models.user import User
from app.services.daily_tasks import claim_task, claim_weekly_challenge, start_focus_session

router = APIRouter()


@router.post("/daily-tasks/{task_key}/claim")
def task_claim(task_key: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    claim_task(db, user.id, task_key)
    return RedirectResponse("/dashboard#daily-missions", 303)


@router.post("/daily-tasks/focus/start")
def focus_start(user: User = Depends(current_user), db: Session = Depends(get_db)):
    start_focus_session(db, user.id)
    return RedirectResponse("/dashboard#daily-missions", 303)


@router.post("/weekly-challenge/claim")
def weekly_claim(user: User = Depends(current_user), db: Session = Depends(get_db)):
    claim_weekly_challenge(db, user.id)
    return RedirectResponse("/dashboard#weekly-challenge", 303)
