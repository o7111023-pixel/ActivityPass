from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from datetime import date
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.models.pass_model import MembershipPass
from app.models.user import User
from app.services.rewards import get_balance

router = APIRouter()


@router.get("/my-codes", response_class=HTMLResponse)
def my_codes(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.main import templates
    passes = db.query(MembershipPass).filter(
        MembershipPass.user_id == user.id,
        MembershipPass.status == "ACTIVE",
    ).order_by(MembershipPass.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="my_codes.html",
        context={
            "request": request,
            "user": user,
            "passes": passes,
            "balance": get_balance(db, user.id),
        },
    )


@router.get("/pass/view/{code}", response_class=HTMLResponse)
def public_pass_view(code: str, request: Request, db: Session = Depends(get_db)):
    from app.main import templates
    p = db.query(MembershipPass).filter(MembershipPass.code == code.strip()).first()
    if not p:
        raise HTTPException(404, "Pass not found")
    if p.status == "ACTIVE" and p.end_date < date.today():
        p.status = "EXPIRED"
        db.commit()
    response = templates.TemplateResponse(
        request=request,
        name="public_pass.html",
        context={"request": request, "pass": p},
    )
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return response
