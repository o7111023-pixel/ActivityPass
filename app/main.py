import os
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.database import Base, engine, SessionLocal
from app.models import User, Provider, Activity, Favorite, Purchase
from app.models.pass_model import MembershipPass
from app.models.wallet import WalletTransaction
from app.security import hash_password
from app.services.rewards import grant_welcome_reward
from app.services.cards import ensure_virtual_card


BASE = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").lower() == "true"
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

allowed_hosts = [
    item.strip()
    for item in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,[::1]",
    ).split(",")
    if item.strip()
]

if ENVIRONMENT == "production" and not PUBLIC_BASE_URL.startswith("https://"):
    raise RuntimeError("PUBLIC_BASE_URL must use HTTPS in production.")


docs_url = "/docs" if ENABLE_DOCS else None
redoc_url = "/redoc" if ENABLE_DOCS else None
openapi_url = "/openapi.json" if ENABLE_DOCS else None

app = FastAPI(
    title="ActivityPass",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    debug=False,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(self), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' https://unpkg.com; "
            "connect-src 'self';"
        )
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        if request.cookies.get("access_token") and not request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


class SameOriginPostMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin:
                origin_value = origin.rstrip("/")
                public_origin = f"{urlsplit(PUBLIC_BASE_URL).scheme}://{urlsplit(PUBLIC_BASE_URL).netloc}".rstrip("/")
                request_origin = f"{request.url.scheme}://{request.url.netloc}".rstrip("/")
                if origin_value not in {public_origin, request_origin}:
                    return HTMLResponse(
                        "<!doctype html><html><body><p>Request unavailable.</p></body></html>",
                        status_code=403,
                    )
        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SameOriginPostMiddleware)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 303:
        location = None

        if exc.headers:
            location = exc.headers.get("Location") or exc.headers.get("location")

        if not location:
            location = "/login"

        return RedirectResponse(
            url=location,
            status_code=303,
        )

    return HTMLResponse(
        "<!doctype html><html><body><p>Request unavailable.</p></body></html>",
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTMLResponse(
        "<!doctype html><html><body><p>Request unavailable.</p></body></html>",
        status_code=422,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never expose exception text, stack traces, environment variables or paths.
    return HTMLResponse(
        "<!doctype html><html><body><p>Request unavailable.</p></body></html>",
        status_code=500,
    )


Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        seed_demo_users = os.getenv("SEED_DEMO_USERS", "true" if ENVIRONMENT != "production" else "false").lower() == "true"
        demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "")
        demo_user_password = os.getenv("DEMO_USER_PASSWORD", "")
        if seed_demo_users and len(demo_admin_password) >= 8 and len(demo_user_password) >= 8:
            if not db.query(User).filter(User.email == "admin@activitypass.demo").first():
                db.add(User(email="admin@activitypass.demo", full_name="Demo Admin", password_hash=hash_password(demo_admin_password), role="ADMIN"))
            if not db.query(User).filter(User.email == "user@activitypass.demo").first():
                db.add(User(email="user@activitypass.demo", full_name="Demo User", password_hash=hash_password(demo_user_password), role="USER"))
            db.commit()
            demo_user = db.query(User).filter(User.email == "user@activitypass.demo").first()
            if demo_user:
                grant_welcome_reward(db, demo_user.id)
                ensure_virtual_card(db, demo_user)

        if db.query(Provider).count() == 0:
            catalog = [
                ("PowerGym Erfurt", "Fitness", "Modern gym with strength, cardio and group training.", "Anger 1", "Erfurt", "gym@activitypass.demo"),
                ("Flow Yoga Studio", "Yoga", "Yoga, mobility and meditation classes.", "Bahnhofstraße 10", "Erfurt", "yoga@activitypass.demo"),
                ("City Pool", "Swimming", "Swimming lanes, leisure pool and aqua fitness.", "Nordbad 5", "Erfurt", "pool@activitypass.demo"),
                ("Ice Arena", "Entertainment", "Indoor ice skating and family sessions.", "Sportpark 2", "Erfurt", "ice@activitypass.demo"),
                ("DanceLab Erfurt", "Dance", "Dance classes from beginner to advanced.", "Krämerbrücke 8", "Erfurt", "dance@activitypass.demo"),
                ("ClimbZone", "Climbing", "Bouldering and climbing sessions.", "Gewerbestraße 12", "Erfurt", "climb@activitypass.demo"),
                ("Fight Club Erfurt", "Martial Arts", "Boxing, kickboxing and self-defence training.", "Sportweg 4", "Erfurt", "fight@activitypass.demo"),
                ("Music House", "Music", "Guitar, piano, drums and group music workshops.", "Domplatz 7", "Erfurt", "music@activitypass.demo"),
                ("Art Studio", "Art", "Drawing, painting and creative workshops.", "Kunstgasse 3", "Erfurt", "art@activitypass.demo"),
                ("City Bowling", "Entertainment", "Bowling lanes and social game nights.", "Weimarische Straße 20", "Erfurt", "bowling@activitypass.demo"),
                ("Tennis Park", "Sports", "Indoor and outdoor tennis courts.", "Parkallee 6", "Erfurt", "tennis@activitypass.demo"),
                ("Badminton Club", "Sports", "Badminton courts and coached sessions.", "Sportzentrum 9", "Erfurt", "badminton@activitypass.demo"),
                ("Run Club", "Fitness", "Group running for different levels.", "Hirschgarten", "Erfurt", "run@activitypass.demo"),
                ("Pilates House", "Fitness", "Pilates and core-strength classes.", "Lange Brücke 15", "Erfurt", "pilates@activitypass.demo"),
                ("Cooking Lab", "Education", "Practical cooking and food workshops.", "Küche 21", "Erfurt", "cooking@activitypass.demo"),
                ("Photography Walks", "Art", "Guided city photography workshops.", "Fischmarkt 1", "Erfurt", "photo@activitypass.demo"),
                ("Theatre Workshop", "Culture", "Acting, improvisation and stage practice.", "Theaterplatz 1", "Erfurt", "theatre@activitypass.demo"),
                ("Board Game Café", "Entertainment", "Board game evenings and strategy sessions.", "Kettenstraße 5", "Erfurt", "games@activitypass.demo"),
                ("Meditation Room", "Wellness", "Guided meditation and breathing sessions.", "Ruheweg 2", "Erfurt", "meditation@activitypass.demo"),
                ("Table Tennis Club", "Sports", "Table tennis practice and open play.", "Sporthalle 3", "Erfurt", "tabletennis@activitypass.demo"),
            ]
            providers = []
            for row in catalog:
                providers.append(
                    Provider(
                        name=row[0], category=row[1], description=row[2],
                        address=row[3], city=row[4], organizer_email=row[5]
                    )
                )
            db.add_all(providers)
            db.commit()

            plans = [
                (0, "Gym Monthly", "Fitness", 4000, "", "06:00", "23:00", 0),
                (0, "Gym Student Monthly", "Fitness", 3000, "", "08:00", "21:00", 0),
                (1, "Friday Yoga", "Yoga", 2500, "FRI", "17:00", "18:30", 0),
                (1, "Yoga Unlimited", "Yoga", 3500, "MON,TUE,WED,THU,FRI", "07:00", "20:00", 0),
                (2, "Saturday Swimming", "Swimming", 3000, "SAT", "10:00", "12:00", 0),
                (2, "Pool 10 Visits", "Swimming", 2500, "", "08:00", "20:00", 10),
                (3, "Weekend Ice Skating", "Entertainment", 1500, "SAT,SUN", "14:00", "18:00", 10),
                (3, "Ice Skating Unlimited", "Entertainment", 2500, "SAT,SUN", "10:00", "20:00", 0),
                (4, "Dance Monthly", "Dance", 2800, "TUE,THU", "18:00", "21:00", 0),
                (4, "Friday Dance", "Dance", 1800, "FRI", "18:00", "20:00", 0),
                (5, "Climbing Monthly", "Climbing", 4500, "", "09:00", "22:00", 0),
                (5, "Climbing 10 Visits", "Climbing", 3000, "", "09:00", "22:00", 10),
                (6, "Boxing Monthly", "Martial Arts", 3800, "MON,WED,FRI", "18:00", "21:00", 0),
                (6, "Kickboxing 10 Visits", "Martial Arts", 3200, "", "18:00", "21:00", 10),
                (7, "Music Club", "Music", 2200, "TUE", "18:00", "20:00", 0),
                (7, "Guitar Workshop", "Music", 1800, "SAT", "11:00", "13:00", 4),
                (8, "Art Monthly", "Art", 2400, "WED", "17:00", "20:00", 0),
                (8, "Painting Workshop", "Art", 1600, "SAT", "14:00", "17:00", 4),
                (9, "Bowling 8 Games", "Entertainment", 2000, "", "16:00", "22:00", 8),
                (9, "Bowling Monthly", "Entertainment", 3200, "FRI,SAT", "16:00", "23:00", 0),
                (10, "Tennis Monthly", "Sports", 4200, "", "07:00", "22:00", 0),
                (10, "Tennis 8 Visits", "Sports", 3000, "", "07:00", "22:00", 8),
                (11, "Badminton Monthly", "Sports", 3500, "MON,WED,FRI", "17:00", "22:00", 0),
                (11, "Badminton 10 Visits", "Sports", 2800, "", "17:00", "22:00", 10),
                (12, "Run Club", "Fitness", 1200, "TUE,THU", "18:30", "20:00", 0),
                (13, "Pilates Monthly", "Fitness", 3000, "MON,WED", "17:00", "20:00", 0),
                (14, "Cooking Workshop", "Education", 2200, "SAT", "12:00", "15:00", 4),
                (15, "Photography Walk", "Art", 1500, "SUN", "10:00", "13:00", 4),
                (16, "Theatre Workshop", "Culture", 2600, "THU", "18:00", "20:30", 0),
                (17, "Board Game Club", "Entertainment", 1000, "FRI", "18:00", "23:00", 0),
                (18, "Meditation Monthly", "Wellness", 1800, "MON,THU", "18:00", "19:30", 0),
                (19, "Table Tennis Monthly", "Sports", 2700, "TUE,THU", "17:00", "21:00", 0),
            ]
            for provider_id, name, cat, price, days, start, end, limit in plans:
                provider = providers[provider_id]
                db.add(
                    Activity(
                        provider_id=provider.id, name=name, category=cat,
                        description=provider.description, price=price,
                        duration_days=30, schedule_days=days,
                        start_time=start, end_time=end, max_visits=limit,
                    )
                )
            db.commit()

        premium = [
            ("Royal Golf Club Erfurt", "Premium", "18-hole golf, driving range and clubhouse access for a premium month.", "Golfallee 70", "Erfurt", "golf@activitypass.demo", "Golf Monthly", 70000, "SAT,SUN", "08:00", "20:00"),
            ("Skyline Spa", "Wellness", "Premium spa, sauna and relaxation sessions.", "Panoramaweg 21", "Erfurt", "spa@activitypass.demo", "Premium Spa Monthly", 18000, "MON,TUE,WED,THU,FRI,SAT,SUN", "09:00", "22:00"),
            ("Karting Arena", "Entertainment", "High-speed indoor karting with premium track sessions.", "Rennweg 42", "Erfurt", "karting@activitypass.demo", "Karting Pro", 12000, "FRI,SAT,SUN", "12:00", "22:00"),
            ("Horse Riding Club", "Sports", "Guided horse riding and stable sessions.", "Reitweg 8", "Erfurt", "riding@activitypass.demo", "Horse Riding Monthly", 15000, "SAT,SUN", "09:00", "18:00"),
            ("Private Climbing Hall", "Climbing", "Premium climbing, coaching and advanced routes.", "Felsstraße 17", "Erfurt", "premiumclimb@activitypass.demo", "Climbing Elite", 9000, "MON,TUE,WED,THU,FRI,SAT,SUN", "07:00", "23:00"),
            ("Sailing Experience", "Adventure", "Weekend sailing sessions and practical training.", "Seestraße 11", "Erfurt", "sailing@activitypass.demo", "Sailing Weekend", 22000, "SAT,SUN", "10:00", "17:00"),
            ("Formula Racing Club", "Premium", "Exclusive high-performance racing sessions on a private circuit.", "Rennring 100", "Erfurt", "racing@activitypass.demo", "Racing Elite", 100000, "SAT,SUN", "09:00", "18:00"),
            ("Ocean Surf Retreat", "Premium", "Private surf coaching, premium equipment and weekend ocean sessions.", "Surf Coast 50", "Erfurt", "surf@activitypass.demo", "Surfing Retreat", 50000, "SAT,SUN", "08:00", "18:00"),
            ("Private Yacht Weekend", "Premium", "Luxury yacht experience with a private weekend itinerary.", "Marina 50", "Erfurt", "yacht@activitypass.demo", "Yacht Weekend", 50000, "SAT,SUN", "10:00", "19:00"),
            ("Alpine Adventure", "Premium", "Exclusive mountain adventure with premium guided access.", "Alpenweg 75", "Erfurt", "alpine@activitypass.demo", "Alpine Elite", 75000, "SAT,SUN", "07:00", "18:00"),
        ]
        for row in premium:
            provider = db.query(Provider).filter(Provider.name == row[0]).first()
            if not provider:
                provider = Provider(
                    name=row[0], category=row[1], description=row[2],
                    address=row[3], city=row[4], organizer_email=row[5],
                )
                db.add(provider)
                db.commit()
            if not db.query(Activity).filter(
                Activity.name == row[6], Activity.provider_id == provider.id
            ).first():
                db.add(
                    Activity(
                        provider_id=provider.id, name=row[6], category=row[1],
                        description=row[2], price=row[7], duration_days=30,
                        schedule_days=row[8], start_time=row[9], end_time=row[10],
                        max_visits=0,
                    )
                )
        db.commit()
    finally:
        db.close()


seed()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse("/dashboard", 303)
    return RedirectResponse("/login", 303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    from app.dependencies import current_user
    from app.services.rewards import claim_daily_reward, get_balance
    from app.services.daily_tasks import get_task_state, weekly_challenge_state

    db = SessionLocal()
    try:
        user = current_user(request, db)
        claimed, balance, streak = claim_daily_reward(db, user.id)
        passes_count = db.query(MembershipPass).filter(
            MembershipPass.user_id == user.id
        ).count()
        txs = db.query(WalletTransaction).filter(
            WalletTransaction.user_id == user.id
        ).all()
        earned = sum(t.amount for t in txs if t.amount > 0)
        spent = sum(-t.amount for t in txs if t.amount < 0)
        xp = (
            len([t for t in txs if t.transaction_type == "DAILY_REWARD"]) * 100
            + len([t for t in txs if t.transaction_type == "PURCHASE"]) * 250
            + len([t for t in txs if t.transaction_type in ("TASK_REWARD", "WEEKLY_REWARD")]) * 150
        )
        level = max(1, xp // 1000 + 1)
        fav_ids = {
            x.activity_id
            for x in db.query(Favorite).filter(Favorite.user_id == user.id).all()
        }
        activities = db.query(Activity).filter(Activity.is_active == True).all()
        recommendations = sorted(
            activities,
            key=lambda a: (0 if a.id in fav_ids else 1, -a.id),
        )[:6]
        weekly = weekly_challenge_state(db, user.id)
        daily_tasks = get_task_state(db, user.id)
        challenge_count = weekly["count"]
        achievements = [
            {"icon": "🔥", "title": "Streak Starter", "text": "Reach 3 consecutive days", "unlocked": streak >= 3},
            {"icon": "🎟", "title": "First Pass", "text": "Buy your first membership", "unlocked": passes_count >= 1},
            {"icon": "🏃", "title": "Active Person", "text": "Own 5 memberships", "unlocked": passes_count >= 5},
            {"icon": "💰", "title": "AP Collector", "text": "Earn 10,000 AP", "unlocked": earned >= 10000},
            {"icon": "⭐", "title": "Explorer", "text": "Reach Level 5", "unlocked": level >= 5},
            {"icon": "💎", "title": "Premium Dreamer", "text": "Explore premium experiences", "unlocked": any(t.transaction_type == "PURCHASE" and "Golf" in (t.description or "") for t in txs)},
        ]
        notifications = [
            {"icon": "🔥", "text": f"You are on a {streak}-day streak. Today's reward is {700 * streak:,} AP."},
            {"icon": "💳", "text": f"Your wallet balance is {balance:,} AP."},
            {"icon": "🎯", "text": f"Weekly challenge: {challenge_count}/3 different activities explored."},
            {"icon": "📋", "text": f"Today: {sum(1 for task in daily_tasks if task['claimed'])}/{len(daily_tasks)} daily missions claimed."},
        ]
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "user": user,
                "balance": balance,
                "claimed": claimed,
                "streak": streak,
                "active_passes": passes_count,
                "achievements": achievements,
                "level": level,
                "xp": xp,
                "recommendations": recommendations,
                "challenge_count": challenge_count,
                "challenge_progress": challenge_count * 100 // 3,
                "notifications": notifications,
                "earned": earned,
                "spent": spent,
                "daily_tasks": daily_tasks,
                "weekly": weekly,
            },
        )
    finally:
        db.close()


from app.api import auth, activities, passes, scanner, admin, wallet, profile, tasks, codes

app.include_router(auth.router)
app.include_router(activities.router)
app.include_router(passes.router)
app.include_router(scanner.router)
app.include_router(admin.router)
app.include_router(wallet.router)
app.include_router(profile.router)
app.include_router(tasks.router)
app.include_router(codes.router)
