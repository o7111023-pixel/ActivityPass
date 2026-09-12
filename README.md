# ActivityPass

ActivityPass is a portfolio-ready FastAPI web application that demonstrates a modern membership platform built around **virtual Activity Points (AP)**.

Users register, receive a one-time welcome balance, build a daily activity streak, discover memberships, buy them with virtual AP, and use QR/barcode passes for entry. Organizers can validate passes with a camera scanner or a manual code.

> **Portfolio / educational project:** AP is virtual demo credit. There are no real-money payments, bank cards, or financial transactions.

## Highlights

- FastAPI + SQLAlchemy architecture
- SQLite for local development and PostgreSQL for deployment
- JWT authentication stored in an HttpOnly session cookie
- USER / ADMIN roles
- Virtual AP wallet and 16-digit ActivityPass account number
- One-time registration reward: **7,500 AP**
- Daily streak rewards: **700 AP × consecutive day number**, with no cap
- Daily missions, focus sessions, weekly challenge and achievements
- Activity catalog with favorites and premium experiences
- Membership purchase flow with balance validation
- Active memberships disappear from Explore and return after expiry
- Purchase history remains available in the database
- QR + Code 128 membership codes
- Public, mobile-friendly pass verification page
- Organizer scanner with camera support via ZXing
- Secure production configuration and generic error responses
- Docker + PostgreSQL local stack
- Git/GitHub-ready repository files
- Automated unit, security and HTTP integration tests

## User flow

1. Open ActivityPass.
2. Without a session, the application shows only the authentication area.
3. Register or sign in.
4. Registration grants 7,500 AP once.
5. From the next calendar day, an authenticated day can claim the daily streak reward.
6. Explore memberships and open an activity detail page.
7. Purchase a membership using the user's own ActivityPass account number.
8. The purchased activity is hidden from Explore while the membership is active.
9. The membership remains available in **My Passes** and **My Codes**.
10. The pass contains a QR code and Code 128 barcode pointing to the public verification URL.
11. An organizer can scan the code and validate date, day, time and visit limits.
12. After the validity period ends, the pass becomes EXPIRED and the activity becomes purchasable again.

## Reward rules

- Registration: **+7,500 AP**, exactly once.
- Registration day does **not** receive a daily reward.
- Day 1: **+700 AP**.
- Day 2: **+1,400 AP**.
- Day 3: **+2,100 AP**.
- The reward continues to grow by 700 AP for each consecutive day.
- Missing a calendar day resets the streak to day 1.
- Refreshing pages cannot multiply the reward for the same day.

## Security model

This project is hardened for a public portfolio/demo deployment. It is not presented as a guarantee that every possible production attack is impossible.

### Application-level protections

- Production requires `ACTIVITYPASS_SECRET_KEY` with at least 32 characters.
- Development generates a process-local secret if one is not supplied.
- JWT tokens expire after 12 hours.
- Authentication cookies are `HttpOnly` and `SameSite=Lax`.
- `COOKIE_SECURE=true` is supported for HTTPS deployments.
- Trusted Host validation is enabled through `ALLOWED_HOSTS`.
- Production HSTS is enabled.
- CSP, frame protection, MIME sniffing protection, referrer policy and permissions policy are enabled.
- Swagger, ReDoc and OpenAPI can be disabled with `ENABLE_DOCS=false`.
- State-changing requests perform an Origin check when an Origin header is supplied.
- Generic 4xx/5xx responses do not expose Python exception text, stack traces, filesystem paths, environment variables or internal route descriptions.
- Unknown routes return a minimal generic response rather than revealing the requested page name.
- The public pass page has `noindex,nofollow,noarchive` and `Cache-Control: no-store`.
- The public pass page intentionally exposes only the information required to verify a pass: activity, provider, location, schedule, validity, description and pass code. It does not expose the user's email, password, wallet balance or profile.
- Demo users are seeded only when `SEED_DEMO_USERS=true`; production defaults this setting to `false`.
- The Docker container runs as a non-root user.
- `.env`, databases, generated code images and local secrets are excluded from Git.

### Important production boundary

The application is suitable as a portfolio project. For a real commercial deployment, add platform/WAF rate limiting, Redis-backed throttling, full CSRF tokens for every state-changing form, Alembic migrations, centralized logging/monitoring, secret management and a managed object store for generated assets.

## Project structure

```text
ActivityPass/
├── app/
│   ├── api/                 # authentication, activities, passes, scanner, wallet, admin, tasks
│   ├── models/              # SQLAlchemy models
│   ├── services/            # rewards, cards, QR/barcodes, daily tasks
│   ├── database.py
│   ├── dependencies.py
│   ├── security.py
│   └── main.py
├── templates/               # Jinja2 pages
├── static/
│   ├── css/
│   ├── js/
│   └── generated/          # local generated QR/barcode files
├── tests/                   # unit, security and HTTP integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
├── .env.production.example
├── .gitignore
├── .gitattributes
└── vercel.json
```

## Local setup in PyCharm

### 1. Create a virtual environment

Use PyCharm's Python interpreter settings or:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

For the application:

```powershell
pip install -r requirements.txt
```

For development and tests:

```powershell
pip install -r requirements-dev.txt
```

### 3. Configure local environment

Copy `.env.example` to `.env` and keep:

```text
ENVIRONMENT=development
DATABASE_URL=sqlite:///./activitypass.db
ACTIVITYPASS_SECRET_KEY=replace-with-a-random-secret-at-least-32-characters
PUBLIC_BASE_URL=http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
COOKIE_SECURE=false
ENABLE_DOCS=true
SEED_DEMO_USERS=true
```

### 4. Run

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Swagger is available locally while `ENABLE_DOCS=true`:

```text
http://127.0.0.1:8000/docs
```

## Development demo accounts

Demo accounts are for **local development only** and are disabled by default in production. The repository does not contain hard-coded demo passwords.

In your local `.env`, choose your own values:

```text
SEED_DEMO_USERS=true
DEMO_USER_PASSWORD=your-local-user-password
DEMO_ADMIN_PASSWORD=your-local-admin-password
```

The demo emails are `user@activitypass.demo` and `admin@activitypass.demo`. Never deploy these demo accounts to a public production database. Use `SEED_DEMO_USERS=false` in production.

## Testing

Run the complete test suite:

```powershell
python -m pytest -q
```

The suite covers:

- one-time 7,500 AP welcome reward
- registration-day reward exclusion
- 700 AP daily reward
- refresh/idempotency protection
- streak growth
- streak reset after a missed day
- password hashing and verification
- production secret requirements
- production demo-user protection
- secret/environment Git rules
- security headers
- generic error pages
- public pass privacy/no-index behavior
- CSP-friendly scanner JavaScript
- authentication cookie properties
- disabled API documentation
- HTTP authentication and protected-page behavior
- cross-origin POST rejection
- public pass access without exposing account data

The HTTP integration tests require the normal runtime dependencies from `requirements.txt`; they are not intended to be silently skipped in a correctly installed local environment. The repository still contains the complete integration suite for normal development environments.

### Verification in the build environment

The project was syntax-compiled and the available tests were executed after the security changes. The isolated build environment does not contain every optional runtime package, so some HTTP integration tests are skipped there by design. In the normal project environment, install `requirements-dev.txt` and run the complete suite with `python -m pytest -q`.

The test suite is intentionally designed to fail on regressions in authentication, rewards, access control, error disclosure, security headers, cookie settings, public-pass privacy, cross-origin state changes and accidental exposure of project files.

## Docker + PostgreSQL

Create `.env` from `.env.example` and provide database credentials for the compose stack, then run:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Stop:

```powershell
docker compose down
```

Delete the PostgreSQL volume only when you intentionally want to remove local database data:

```powershell
docker compose down -v
```

The Docker image uses Python 3.12-slim and runs the application as a non-root user.

## Git / GitHub

```powershell
git init
git add .
git commit -m "feat: complete ActivityPass portfolio app"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

The repository intentionally keeps environment templates while ignoring real `.env` files, local databases, generated PNGs, IDE files and caches.

## Vercel deployment

The project includes a Vercel configuration and can be adapted to Vercel's Python runtime.

Before a public deployment:

1. Use a managed PostgreSQL database rather than SQLite.
2. Set `DATABASE_URL` in Vercel Environment Variables.
3. Set a strong random `ACTIVITYPASS_SECRET_KEY`.
4. Set `ENVIRONMENT=production`.
5. Set `PUBLIC_BASE_URL=https://your-real-domain`.
6. Configure `ALLOWED_HOSTS` for the real hostname and required Vercel hostname.
7. Set `COOKIE_SECURE=true`.
8. Set `ENABLE_DOCS=false`.
9. Set `SEED_DEMO_USERS=false`.
10. Use the real HTTPS `PUBLIC_BASE_URL` before generating new QR/barcode passes.

### QR code note

The QR code contains a public pass URL. This is intentional: scanning from an iPhone camera should open the verification page immediately. The URL is a bearer-style pass reference, so it must not contain passwords, JWTs, database credentials or other secrets.

For serverless hosting, generated PNG files should eventually be moved to persistent object storage or replaced with dynamically generated SVG/data URLs. Local filesystem storage should not be treated as durable Vercel storage.

## ActivityPass account number

Every user receives a unique random 16-digit ActivityPass demo account number. It is an internal identifier for the virtual AP wallet, not a bank card. It has no CVV, expiry date or connection to a payment provider.

## Database note

The first portfolio version uses SQLAlchemy `create_all()` for straightforward startup. For a serious long-lived production system, replace schema changes with Alembic migrations and use a controlled seed/setup command.

## License / portfolio use

This project is intended as a personal educational and portfolio demonstration by **Oleh Murachov**.

Technology stack: **Python · FastAPI · SQLAlchemy · Jinja2 · SQLite/PostgreSQL · Docker · pytest**.
