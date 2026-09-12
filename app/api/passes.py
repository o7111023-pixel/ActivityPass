from datetime import date, timedelta
import secrets
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user
from app.models.activity import Activity
from app.models.pass_model import MembershipPass
from app.models.purchase import Purchase
from app.models.user import User
from app.models.virtual_card import VirtualCard
from app.services.codes import generate_codes
from app.services.rewards import claim_daily_reward, get_balance, spend

router=APIRouter()


def sync_expired_passes(db: Session, user_id: int | None = None):
    """Mark passes as expired after their validity date. The history stays in DB."""
    query = db.query(MembershipPass).filter(
        MembershipPass.status == "ACTIVE",
        MembershipPass.end_date < date.today(),
    )
    if user_id is not None:
        query = query.filter(MembershipPass.user_id == user_id)
    changed = False
    for membership in query.all():
        membership.status = "EXPIRED"
        changed = True
    if changed:
        db.commit()


@router.post("/activities/{activity_id}/buy")
def buy(activity_id:int, card_number:str=Form(...), barcode_type:str=Form("CODE128"), user:User=Depends(current_user), db:Session=Depends(get_db)):
    sync_expired_passes(db, user.id)
    a=db.get(Activity,activity_id)
    if not a or not a.is_active: raise HTTPException(404,"Activity not found")
    normalized_card="".join(ch for ch in card_number if ch.isdigit())
    card=db.query(VirtualCard).filter(VirtualCard.user_id==user.id).first()
    if not card or normalized_card != card.card_number:
        return RedirectResponse(f"/activities/{activity_id}?error=Invalid+ActivityPass+account+number",303)
    claim_daily_reward(db,user.id)
    # One active membership per activity; after expiry it becomes purchasable again.
    active_same = db.query(MembershipPass).filter(
        MembershipPass.user_id == user.id,
        MembershipPass.activity_id == a.id,
        MembershipPass.status == "ACTIVE",
        MembershipPass.end_date >= date.today(),
    ).first()
    if active_same:
        return RedirectResponse(f"/activities/{activity_id}?error=You+already+have+an+active+pass+for+this+activity",303)
    code="AP-"+secrets.token_hex(5).upper()
    p=MembershipPass(user_id=user.id,activity_id=a.id,code=code,barcode_type=barcode_type,
                     start_date=date.today(),end_date=date.today()+timedelta(days=a.duration_days))
    db.add(p); db.flush()
    try:
        spend(db,user.id,a.price,f"Purchase: {a.name}",code)
    except ValueError as e:
        db.rollback()
        return RedirectResponse(f"/activities/{activity_id}?error={str(e).replace(' ','+')}",303)
    db.add(Purchase(user_id=user.id,activity_id=a.id,pass_id=p.id,amount=a.price))
    db.commit(); generate_codes(code)
    return RedirectResponse("/my-passes",303)

@router.get("/my-passes",response_class=HTMLResponse)
def my_passes(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from app.main import templates
    sync_expired_passes(db, user.id)
    claim_daily_reward(db,user.id)
    ps=db.query(MembershipPass).filter(MembershipPass.user_id==user.id, MembershipPass.status=="ACTIVE").filter(MembershipPass.user_id==user.id).order_by(MembershipPass.id.desc()).all()
    return templates.TemplateResponse(request=request,name="my_passes.html",context={"request":request,"user":user,"passes":ps,"balance":get_balance(db,user.id)})

@router.get("/passes/{pass_id}",response_class=HTMLResponse)
def pass_page(pass_id:int,request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from app.main import templates
    sync_expired_passes(db, user.id)
    p=db.get(MembershipPass,pass_id)
    if not p or p.user_id!=user.id: raise HTTPException(404,"Pass not found")
    return templates.TemplateResponse(request=request,name="pass_detail.html",context={"request":request,"user":user,"pass":p,"balance":get_balance(db,user.id)})
