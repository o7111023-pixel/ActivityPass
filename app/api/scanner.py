from datetime import date, datetime
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import admin_user
from app.models.checkin import CheckIn
from app.models.pass_model import MembershipPass
from app.models.user import User

router=APIRouter()

@router.get("/scanner",response_class=HTMLResponse)
def page(request:Request,user:User=Depends(admin_user)):
    from app.main import templates
    return templates.TemplateResponse(request=request,name="scanner.html",context={"request":request,"result":None})

@router.post("/scanner",response_class=HTMLResponse)
def scan(code:str=Form(...),request:Request=None,user:User=Depends(admin_user),db:Session=Depends(get_db)):
    from app.main import templates
    raw = code.strip()
    parsed = urlparse(raw)
    if parsed.path.startswith("/pass/view/"):
        raw = parsed.path.rstrip("/").split("/")[-1]
    p=db.query(MembershipPass).filter(MembershipPass.code==raw).first()
    result={"ok":False,"title":"INVALID","message":"Pass not found."}
    if p:
        a=p.activity; now=datetime.now().strftime("%H:%M"); today=date.today()
        days=[x.strip().upper()[:3] for x in a.schedule_days.split(",") if x.strip()]
        day_ok=not days or today.strftime("%a").upper()[:3] in days
        time_ok=a.start_time<=now<=a.end_time
        if p.status!="ACTIVE": result={"ok":False,"title":p.status,"message":"Pass is not active."}
        elif today<p.start_date or today>p.end_date: result={"ok":False,"title":"EXPIRED","message":"Pass has expired."}
        elif not day_ok: result={"ok":False,"title":"WRONG DAY","message":f"Allowed: {a.schedule_days}"}
        elif not time_ok: result={"ok":False,"title":"WRONG TIME","message":f"Allowed: {a.start_time}–{a.end_time}"}
        elif a.max_visits and p.visits_used>=a.max_visits: result={"ok":False,"title":"NO VISITS","message":"Visit limit reached."}
        else:
            p.visits_used+=1
            db.add(CheckIn(pass_id=p.id,provider_id=a.provider_id,result="SUCCESS",message="Access granted"))
            db.commit()
            result={"ok":True,"title":"VALID PASS","message":f"{a.name} · access granted · visit #{p.visits_used}"}
    return templates.TemplateResponse(request=request,name="scanner.html",context={"request":request,"result":result})
