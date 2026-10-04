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
    HIGH_ROLLER_UNLOCK_BALANCE,
    RISK_UNLOCK_BALANCE,
    SAFE_UNLOCK_BALANCE,
    calculate_win,
    get_highest_balance,
    get_wheel_level,
    is_fortune_wheel_unlocked,
    is_high_roller_unlocked,
    is_risk_wheel_unlocked,
    spin_wheel,
)
from app.services.rewards import get_balance


router = APIRouter(
    prefix="/api/fortune-wheel",
    tags=["Fortune Wheel"],
)

templates = Jinja2Templates(directory="templates")


# ============================================================
# ALLOWED BETS
# ============================================================

ALLOWED_BETS = {
    500,
    1_500,
    2_500,
    5_000,
    7_500,
    10_000,
    20_000,
    50_000,
    70_000,
    80_000,
    99_000,
}


# ============================================================
# SPIN
# ============================================================

@router.post("/spin")
def play_fortune_wheel(
    bet_amount: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if bet_amount not in ALLOWED_BETS:
        raise HTTPException(
            status_code=400,
            detail="Invalid bet amount.",
        )

    # --------------------------------------------------------
    # Determine wheel level
    # --------------------------------------------------------

    wheel_level = get_wheel_level(bet_amount)

    # --------------------------------------------------------
    # Check access to the selected wheel
    #
    # SAFE:
    # highest balance >= 30,000 AP
    #
    # RISK:
    # highest balance >= 100,000 AP
    #
    # HIGH ROLLER:
    # highest balance >= 500,000 AP
    # --------------------------------------------------------

    if wheel_level == "SAFE":
        if not is_fortune_wheel_unlocked(db, user.id):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Safe Wheel is locked. "
                    "Reach 30,000 AP at least once first."
                ),
            )

    elif wheel_level == "RISK":
        if not is_risk_wheel_unlocked(db, user.id):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Risk Wheel is locked. "
                    "Reach 100,000 AP at least once first."
                ),
            )

    elif wheel_level == "HIGH_ROLLER":
        if not is_high_roller_unlocked(db, user.id):
            raise HTTPException(
                status_code=403,
                detail=(
                    "High Roller is locked. "
                    "Reach 500,000 AP at least once first."
                ),
            )

    # --------------------------------------------------------
    # Check current balance
    # --------------------------------------------------------

    balance = get_balance(db, user.id)

    if balance < bet_amount:
        raise HTTPException(
            status_code=400,
            detail="Not enough AP points.",
        )

    # --------------------------------------------------------
    # Spin
    # --------------------------------------------------------

    selected_segment = spin_wheel(bet_amount)

    sector = selected_segment["sector"]
    multiplier = selected_segment["multiplier"]
    fixed_win = selected_segment["fixed_win"]

    win_amount = calculate_win(
        bet_amount=bet_amount,
        multiplier=multiplier,
        fixed_win=fixed_win,
    )

    # --------------------------------------------------------
    # Calculate new balance
    #
    # First subtract the bet,
    # then add the payout.
    # --------------------------------------------------------

    new_balance = balance - bet_amount + win_amount

    # --------------------------------------------------------
    # Save spin
    # --------------------------------------------------------

    spin = FortuneWheelSpin(
        user_id=user.id,
        bet_amount=bet_amount,
        multiplier=multiplier,
        win_amount=win_amount,
    )

    db.add(spin)
    db.flush()

    # --------------------------------------------------------
    # Save wallet transaction
    # --------------------------------------------------------

    if fixed_win is not None:
        result_name = f"+{fixed_win:,} AP"
    else:
        result_name = f"{multiplier}x"

    transaction = WalletTransaction(
        user_id=user.id,
        amount=win_amount - bet_amount,
        balance_after=new_balance,
        transaction_type="FORTUNE_WHEEL",
        description=(
            f"Fortune Wheel · "
            f"{wheel_level} · "
            f"{result_name}"
        ),
        reference=f"FORTUNE-{spin.id}",
    )

    db.add(transaction)
    db.commit()

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "success": True,
        "sector": sector,
        "wheel_level": wheel_level,
        "bet": bet_amount,
        "multiplier": multiplier,
        "fixed_win": fixed_win,
        "win": win_amount,
        "balance": new_balance,
    }


# ============================================================
# FORTUNE WHEEL PAGE
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
def fortune_wheel_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Current balance
    # --------------------------------------------------------

    balance = get_balance(
        db,
        user.id,
    )

    # --------------------------------------------------------
    # Highest balance ever reached
    # --------------------------------------------------------

    highest_balance = get_highest_balance(
        db,
        user.id,
    )

    # --------------------------------------------------------
    # Wheel access
    # --------------------------------------------------------

    safe_unlocked = is_fortune_wheel_unlocked(
        db,
        user.id,
    )

    risk_unlocked = is_risk_wheel_unlocked(
        db,
        user.id,
    )

    high_roller_unlocked = is_high_roller_unlocked(
        db,
        user.id,
    )

    # --------------------------------------------------------
    # Template
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="fortune_wheel.html",
        context={
            "request": request,
            "user": user,
            "balance": balance,
            "highest_balance": highest_balance,

            # Wheel access
            "unlocked": safe_unlocked,
            "safe_unlocked": safe_unlocked,
            "risk_unlocked": risk_unlocked,
            "high_roller_unlocked": high_roller_unlocked,

            # Unlock requirements
            "safe_unlock_balance": SAFE_UNLOCK_BALANCE,
            "risk_unlock_balance": RISK_UNLOCK_BALANCE,
            "high_roller_unlock_balance": HIGH_ROLLER_UNLOCK_BALANCE,

            # Backward-compatible value
            "unlock_balance": SAFE_UNLOCK_BALANCE,
        },
    )
