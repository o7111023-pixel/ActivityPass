from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
from app.database import get_db
from app.models.user import User
from app.security import create_access_token, hash_password, verify_password
from app.services.rewards import grant_welcome_reward, claim_daily_reward
from app.services.cards import ensure_virtual_card

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    from app.main import templates
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@router.post("/login")
def login(email: str=Form(...), password: str=Form(...), db: Session=Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=Invalid+credentials", 303)
    claim_daily_reward(db, user.id)
    r = RedirectResponse("/dashboard", 303)
    r.set_cookie(
        "access_token",
        create_access_token(user.id),
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        max_age=12 * 60 * 60,
        path="/",
    )
    return r

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    from app.main import templates
    return templates.TemplateResponse(request=request, name="register.html", context={"request": request})

@router.post("/register")
def register(full_name: str=Form(...), email: str=Form(...), password: str=Form(...), db: Session=Depends(get_db)):
    if len(full_name.strip()) < 2 or len(full_name.strip()) > 100:
        return RedirectResponse("/register?error=Invalid+name", 303)
    if len(password) < 8 or len(password) > 128:
        return RedirectResponse("/register?error=Password+must+be+8-128+characters", 303)
    email=email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        return RedirectResponse("/register?error=Email+already+registered", 303)
    u=User(email=email, full_name=full_name.strip(), password_hash=hash_password(password))
    db.add(u); db.commit()
    grant_welcome_reward(db, u.id)
    ensure_virtual_card(db, u)
    r=RedirectResponse("/dashboard", 303)
    r.set_cookie(
        "access_token",
        create_access_token(u.id),
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        max_age=12 * 60 * 60,
        path="/",
    )
    return r

@router.post("/logout")
def logout():
    r=RedirectResponse("/", 303); r.delete_cookie("access_token"); return r
