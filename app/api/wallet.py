from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.rewards import claim_daily_reward, get_balance
from app.services.cards import ensure_virtual_card, masked_card

router=APIRouter()

@router.get("/wallet", response_class=HTMLResponse)
def wallet(request: Request, user: User=Depends(current_user), db: Session=Depends(get_db)):
    from app.main import templates
    claim_daily_reward(db, user.id)
    card=ensure_virtual_card(db, user)
    transactions=db.query(WalletTransaction).filter(
        WalletTransaction.user_id==user.id
    ).order_by(WalletTransaction.id.desc()).limit(50).all()
    return templates.TemplateResponse(request=request,name="wallet.html",context={
        "request":request,"balance":get_balance(db,user.id),"transactions":transactions,"card":card,"card_display":masked_card(card.card_number)
    })
