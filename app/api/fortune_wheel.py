from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.models.fortune_wheel import FortuneWheelSpin
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.fortune_wheel import (
    calculate_win,
    is_fortune_wheel_unlocked,
    spin_wheel,
)
from app.services.rewards import get_balance


router = APIRouter(
    prefix="/api/fortune-wheel",
    tags=["Fortune Wheel"],
)

templates = Jinja2Templates(directory="templates")


ALLOWED_BETS = {
    10_000,
    20_000,
    50_000,
}


@router.post("/spin")
def play_fortune_wheel(
    bet_amount: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not is_fortune_wheel_unlocked(db, user.id):
        raise HTTPException(
            status_code=403,
            detail="Fortune Wheel is locked. Reach 30,000 AP first.",
        )

    if bet_amount not in ALLOWED_BETS:
        raise HTTPException(
            status_code=400,
            detail="Invalid bet amount.",
        )

    balance = get_balance(db, user.id)

    if balance < bet_amount:
        raise HTTPException(
            status_code=400,
            detail="Not enough AP points.",
        )

    multiplier = spin_wheel()

    win_amount = calculate_win(
        bet_amount,
        multiplier,
    )

    new_balance = balance - bet_amount + win_amount

    spin = FortuneWheelSpin(
        user_id=user.id,
        bet_amount=bet_amount,
        multiplier=multiplier,
        win_amount=win_amount,
    )

    db.add(spin)
    db.flush()

    transaction = WalletTransaction(
        user_id=user.id,
        amount=win_amount - bet_amount,
        balance_after=new_balance,
        transaction_type="FORTUNE_WHEEL",
        description=f"Fortune Wheel · {multiplier}x",
        reference=f"FORTUNE-{spin.id}",
    )

    db.add(transaction)
    db.commit()

    return {
        "success": True,
        "bet": bet_amount,
        "multiplier": multiplier,
        "win": win_amount,
        "balance": new_balance,
    }


@router.get("/", response_class=HTMLResponse)
def fortune_wheel_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    balance = get_balance(db, user.id)

    unlocked = is_fortune_wheel_unlocked(
        db,
        user.id,
    )

    return templates.TemplateResponse(
        request=request,
        name="fortune_wheel.html",
        context={
            "request": request,
            "user": user,
            "balance": balance,
            "unlocked": unlocked,
            "unlock_balance": 30_000,
        },
    )
