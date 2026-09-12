from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token


def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        if request.method == "GET":
            raise HTTPException(status_code=303, headers={"Location": "/login"})
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_id = decode_access_token(token)
        user = db.get(User, user_id)
    except (ValueError, TypeError):
        user = None

    if not user or not user.is_active:
        if request.method == "GET":
            raise HTTPException(status_code=303, headers={"Location": "/login"})
        raise HTTPException(status_code=401, detail="Authentication required")

    return user


def admin_user(user=Depends(current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
