from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import admin_user
from app.models.user import User
from app.models.provider import Provider
from app.models.activity import Activity

router=APIRouter()

@router.get("/admin",response_class=HTMLResponse)
def admin(request:Request,user:User=Depends(admin_user),db:Session=Depends(get_db)):
    from app.main import templates
    return templates.TemplateResponse(request=request,name="admin.html",context={"request":request,
        "users":db.query(User).all(),"providers":db.query(Provider).all(),"activities":db.query(Activity).all()})

@router.post("/admin/providers")
def provider(name:str=Form(...),category:str=Form(...),description:str=Form(...),address:str=Form(...),city:str=Form("Erfurt"),organizer_email:str=Form(...),user=Depends(admin_user),db:Session=Depends(get_db)):
    db.add(Provider(name=name,category=category,description=description,address=address,city=city,organizer_email=organizer_email)); db.commit()
    return RedirectResponse("/admin",303)

@router.post("/admin/activities")
def activity(provider_id:int=Form(...),name:str=Form(...),category:str=Form(...),description:str=Form(...),price:int=Form(...),duration_days:int=Form(30),schedule_days:str=Form(""),start_time:str=Form("09:00"),end_time:str=Form("18:00"),max_visits:int=Form(0),user=Depends(admin_user),db:Session=Depends(get_db)):
    db.add(Activity(provider_id=provider_id,name=name,category=category,description=description,price=price,duration_days=duration_days,schedule_days=schedule_days,start_time=start_time,end_time=end_time,max_visits=max_visits)); db.commit()
    return RedirectResponse("/admin",303)
