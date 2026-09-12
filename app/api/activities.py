from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.models.favorite import Favorite
from app.models.activity_view import ActivityView
from app.models.pass_model import MembershipPass
from app.dependencies import current_user
from app.services.rewards import claim_daily_reward, get_balance

router=APIRouter()

@router.get("/activities", response_class=HTMLResponse)
def activities(request: Request, q: str="", category: str="", favorites_only: int = 0, user: User=Depends(current_user), db: Session=Depends(get_db)):
    from app.main import templates
    query=db.query(Activity).filter(Activity.is_active==True)
    if q: query=query.filter(Activity.name.ilike(f"%{q}%"))
    if category: query=query.filter(Activity.category==category)
    favorites_set={x.activity_id for x in db.query(Favorite).filter(Favorite.user_id==user.id).all()}
    active_pass_activity_ids={x.activity_id for x in db.query(MembershipPass).filter(
        MembershipPass.user_id==user.id, MembershipPass.status=="ACTIVE", MembershipPass.end_date>=date.today()
    ).all()}
    favorites=favorites_set
    items=[a for a in query.all() if a.id not in active_pass_activity_ids]
    if favorites_only:
        items=[a for a in items if a.id in favorites_set]
    items.sort(key=lambda a: (0 if a.id in favorites else 1, -a.id))
    categories=[x[0] for x in db.query(Activity.category).filter(Activity.is_active==True).distinct().order_by(Activity.category).all()]
    return templates.TemplateResponse(request=request, name="activities.html",
        context={"request":request,"user":user,"balance":get_balance(db,user.id),"activities":items,"q":q,"category":category,"favorites":favorites,"categories":categories,"active_pass_activity_ids":active_pass_activity_ids})

@router.post("/activities/{activity_id}/favorite")
def toggle_favorite(activity_id:int, request:Request, user:User=Depends(current_user), db:Session=Depends(get_db)):
    fav=db.query(Favorite).filter(Favorite.user_id==user.id, Favorite.activity_id==activity_id).first()
    if fav: db.delete(fav); state="removed"
    else: db.add(Favorite(user_id=user.id, activity_id=activity_id)); state="added"
    db.commit()
    referer=request.headers.get("referer") or "/activities"
    return RedirectResponse(referer,303)

@router.get("/activities/{activity_id}", response_class=HTMLResponse)
def detail(activity_id:int, request:Request, user:User=Depends(current_user), db:Session=Depends(get_db)):
    from app.main import templates
    a=db.get(Activity, activity_id)
    if not a: raise HTTPException(404,"Activity not found")
    liked=db.query(Favorite).filter(Favorite.user_id==user.id, Favorite.activity_id==activity_id).first() is not None
    view = db.query(ActivityView).filter(ActivityView.user_id == user.id, ActivityView.activity_id == activity_id, ActivityView.view_date == date.today()).first()
    if not view:
        db.add(ActivityView(user_id=user.id, activity_id=activity_id))
        db.commit()
    return templates.TemplateResponse(request=request,name="activity_detail.html",context={"request":request,"user":user,"activity":a,"liked":liked,"balance":get_balance(db,user.id)})

@router.post("/daily-reward")
def daily_reward(user:User=Depends(current_user), db:Session=Depends(get_db)):
    claimed,balance,streak=claim_daily_reward(db,user.id)
    return {"claimed":claimed,"amount":(700*streak if claimed else 0),"balance":balance,"streak":streak}
