from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user
from app.models.user import User
from app.models.pass_model import MembershipPass
from app.services.rewards import claim_daily_reward, get_balance, get_streak, get_recent_checkins

router = APIRouter()

@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.main import templates
    claim_daily_reward(db, user.id)
    passes = db.query(MembershipPass).filter(MembershipPass.user_id == user.id).order_by(MembershipPass.id.desc()).all()
    return templates.TemplateResponse(request=request, name="profile.html", context={
        "request": request, "user": user, "balance": get_balance(db, user.id), "passes": passes
    })

@router.post("/profile")
def update_profile(
    full_name: str = Form(...),
    hobbies: str = Form(""),
    preferred_time: str = Form("Evening"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    user.full_name = full_name.strip() or user.full_name
    user.hobbies = hobbies.strip()
    user.preferred_time = preferred_time
    db.commit()
    return RedirectResponse("/profile?saved=1", 303)

@router.get("/calendar", response_class=HTMLResponse)
def calendar(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.main import templates
    claim_daily_reward(db, user.id)
    passes = db.query(MembershipPass).filter(MembershipPass.user_id == user.id).order_by(MembershipPass.end_date, MembershipPass.id).all()
    streak = get_streak(db, user.id)
    checkins = get_recent_checkins(db, user.id, 28)
    today_reward = 700 * max(streak, 1)
    return templates.TemplateResponse(request=request, name="calendar.html", context={"request": request, "user": user, "balance": get_balance(db,user.id), "passes": passes, "streak": streak, "checkins": checkins, "today_reward": today_reward})
