import secrets
from sqlalchemy.orm import Session
from app.models.virtual_card import VirtualCard

def _random_demo_number() -> str:
    # Prefix 99 makes it visually distinct from a normal bank-card flow.
    # It is an internal ActivityPass demo account identifier only.
    return "99" + "".join(str(secrets.randbelow(10)) for _ in range(14))

def ensure_virtual_card(db: Session, user) -> VirtualCard:
    card = db.query(VirtualCard).filter(VirtualCard.user_id == user.id).first()
    if card:
        return card

    while True:
        number = _random_demo_number()
        if not db.query(VirtualCard).filter(VirtualCard.card_number == number).first():
            break

    card = VirtualCard(
        user_id=user.id,
        card_number=number,
        holder_name=user.full_name.upper()
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card

def masked_card(number: str) -> str:
    return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:]}"
