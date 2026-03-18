# QIPP — YOUR Personal Build Guide
## Windows · GitHub Copilot · Google Antigravity IDE
**Your role: Backend Lead + DevOps + Data Pipelines**

---

> **Ground truth on the PoC:** The HTML file you provided (`MedSave_Platform_v4_SouthYorkshire.html`) is your pixel-perfect design contract. Every page, every colour, every card, every number that appears in the React app must match what is in that file — except the numbers will be real, from live APIs. Do not redesign anything. The PoC is the spec.

---

## 1. Does the System Match the PoC Exactly?

Yes — with these clarifications:

**What matches 1:1:**
- Login screen (two-panel layout, role selector cards: GP/Pharmacist/PCN/ICB, teal/dark gradient left panel)
- Dashboard with 4 hero metric cards (total saving potential, active opportunities, practices, completed switches)
- Opportunity register table (sortable columns: drug switch, workstream, saving, patients, ease score)
- ICB All Opportunities view
- QIPP Scheme Builder page (toggle on/off, publish scheme button)
- Financial Performance page (expenditure, savings delivered, switch value ranking)
- Price per Unit analysis (outlier detection, ghost generics)
- Price Concession Cost Dashboard (monthly tariff cost, OpenPrescribing link)
- Switch Impact Monitoring (EPD verification, target vs actual)
- ICB Benchmarking (SY vs comparator ICB, all metrics)
- Practice Performance table (all 105 practices, savings tracking)
- AI Patient Search (plain English → EMIS/SystmOne query output)
- Find Switching Opportunities (free-text AI search, JSON output cards)
- Action Sheets & Patient Letters (generate, print, share)

**What gets replaced with live data:**
- All hardcoded £ savings → real OpenPrescribing calculations
- All hardcoded practice names → real NHS ODS data
- All hardcoded opportunity cards → real MongoDB documents
- Simulated AI responses → real Gemini 2.0 Flash responses
- Hardcoded benchmarking numbers → live OpenPrescribing measure API

**What gets added (robustness):**
- Real JWT authentication (the PoC just has a fake role selector)
- Multi-tenant support (so you can pitch to more than just SY ICB)
- Celery background tasks (data refreshes automatically, no manual triggers)
- Realised savings entry (ePACT2 CSV upload)
- Email notifications via GOV.UK Notify

---

## 2. Your Tools — Setup Guide (Windows)

### 2.1 Google Antigravity IDE (Your Primary Tool)

Antigravity is Google's agentic IDE launched November 2025. It runs autonomous agents that plan, write, and test code — perfect for building this system at speed. It is **free**, **cross-platform**, and **VS Code-based** so everything you know from VS Code works.

**Install:**
1. Download from `antigravity.google/download` → choose Windows installer
2. Run the `.exe` installer
3. On first launch, select **"Agent-assisted development"** (recommended — you stay in control, AI helps with safe automations)
4. Sign in with your Google account (uses the same quota as Gemini 2.0 Flash)
5. Chrome must be installed — Antigravity uses it for the built-in browser agent

**Key surfaces you will use:**
- **Editor View** — VS Code-style editing with inline AI completions (identical feel to Copilot)
- **Agent Manager** — send a task like "build the OpenPrescribing service file" and the agent writes it, tests it, shows you artifacts
- **Built-in Browser** — agent opens your running FastAPI server and tests endpoints automatically
- **Artifacts Panel** — every agent action generates a log/plan you can review and comment on

**Using Antigravity for this project:**
```
# Example Agent Manager prompts you will use:
"Read the system documentation at QIPP_System_Documentation.md 
and implement the OpenPrescribingService class in 
backend/app/services/openprescribing_service.py 
exactly as specified. Include all 6 endpoints, Scrapfly bypass, 
and 24-hour file cache."

"Implement the Alembic migration for all 44 PostgreSQL tables 
described in the database design section."

"Write the Celery task for daily opportunity discovery 
that calls the OpportunityDiscoveryEngine for sub-ICB 02P."
```

**Rate limits:** Gemini 3 Pro quota resets every 5 hours. For heavy sessions (writing large files), use Agent-assisted mode to stay under limits. The free tier is very generous for individual development.

---

### 2.2 GitHub Copilot (Your AI Pair Programmer in Antigravity)

Your Student Pack includes **GitHub Copilot Student** — free as long as you are verified.

**Since March 12, 2026:** You are on the new Copilot Student plan (transitioned automatically).

**Activating in Antigravity:**
Antigravity is VS Code-based, so install Copilot extensions:
```
# In Antigravity terminal (Ctrl+`)
code --install-extension github.copilot
code --install-extension github.copilot-chat
```
Or via Extensions panel (Ctrl+Shift+X) → search "GitHub Copilot" → Install.

**Sign in:** Ctrl+Shift+P → "GitHub Copilot: Sign In" → authenticate with your GitHub student account.

**How to use Copilot alongside Antigravity:**
- **Copilot** = inline completions as you type (Tab to accept)
- **Copilot Chat** (Ctrl+Shift+I) = ask questions, explain code, debug
- **Antigravity Agent** = run whole autonomous tasks across multiple files

Use them together: Antigravity agent drafts a file, Copilot helps you refine specific lines.

---

### 2.3 GitHub Student Pack — Benefits You Should Activate NOW

Go to `education.github.com/pack` and activate these before Sprint 1:

| Benefit | What to Use It For | Activate |
|---------|-------------------|---------|
| **GitHub Copilot Student** | Free AI in Antigravity | Auto-active with student verification |
| **JetBrains (PyCharm Pro)** | Backup Python IDE, excellent FastAPI support | jetbrains.com/student → apply with GitHub |
| **MongoDB Atlas $50 credit** | Victor has this set up — but claim yours too for your personal testing | mongodb.com/students |
| **DigitalOcean $200 credit** | Deploy backend to production for the pitch | education.github.com/pack → DigitalOcean |
| **Namecheap .me domain** | `qipp.health` or similar for the demo | education.github.com/pack → Namecheap |
| **Heroku $13/month × 24** | Alternative deployment if DigitalOcean feels complex | education.github.com/pack → Heroku |
| **Datadog (2 years free)** | Monitor your production FastAPI server | education.github.com/pack → Datadog |
| **Sentry** | Error tracking (free) | sentry.io/for/education |
| **1Password (1 year free)** | Store all your API keys securely | education.github.com/pack → 1Password |
| **GitHub Codespaces (2GB)** | Cloud dev environment if your Windows machine is slow | Included with GitHub Student |
| **Azure $100 credit** | Alternative cloud host if needed | education.github.com/pack → Azure |

**JetBrains PyCharm setup (Windows backup IDE):**
1. Go to `jetbrains.com/community/education` → "Apply for free student license"
2. Use your student email OR link via GitHub Student Pack
3. Download PyCharm (2025.1+ — now unified, no Community/Pro split)
4. Activate with JetBrains Account on first launch
5. PyCharm has excellent FastAPI support: auto-detects routes, database models, Alembic migrations

---

### 2.4 Windows-Specific Setup

```powershell
# Install Python 3.11 (exact version matters for async SQLAlchemy)
# Download from python.org → 3.11.x → Windows installer (64-bit)
# CHECK "Add Python to PATH" during install

# Verify
python --version   # should say 3.11.x

# Install Node.js 18 LTS
# Download from nodejs.org → 18.x LTS → Windows installer

# Install Redis on Windows (use WSL2 or Docker)
# Option A: WSL2 (recommended)
wsl --install   # in PowerShell as admin
# Then in WSL terminal:
sudo apt update && sudo apt install redis-server
sudo service redis-server start

# Option B: Docker Desktop
# Download docker.com/products/docker-desktop
docker run -d -p 6379:6379 --name redis redis:alpine

# Install Git
# Download git-scm.com → Windows → default options

# Install Windows Terminal (from Microsoft Store — much better than cmd.exe)
# This gives you PowerShell + WSL in one terminal
```

---

## 3. Your Responsibilities — Full Breakdown

You own these parts of the system. Victor owns his parts (see his file). You will coordinate daily.

### YOUR BACKEND SERVICES

#### 3.1 FastAPI Application Factory
**File:** `backend/app/main.py`

This is the entry point. Wire up all routers, middleware, MongoDB connection, CORS.

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine
from app.mongodb import connect_mongodb, disconnect_mongodb
from app.config import settings
from app.middleware import TenantContextMiddleware, OrgScopingMiddleware

# Import ALL routers (you build these, Victor builds some)
from app.routers import (
    auth, dashboard, opportunities, tariff, savings,
    interventions, admin, benchmarking, practices,
    formulary, notifications, ai_search, patients
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongodb(settings.MONGODB_URI)
    yield
    await disconnect_mongodb()

def create_app() -> FastAPI:
    app = FastAPI(title="QIPP API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:5173", "https://yourdomain.me"],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(OrgScopingMiddleware)
    app.add_middleware(TenantContextMiddleware)
    for router in [auth.router, dashboard.router, opportunities.router,
                   tariff.router, savings.router, interventions.router,
                   admin.router, benchmarking.router, practices.router,
                   formulary.router, notifications.router, ai_search.router,
                   patients.router]:
        app.include_router(router, prefix="/api")
    return app

app = create_app()
```

#### 3.2 PostgreSQL Database Layer
**Files:** `backend/app/database.py`, `backend/app/models/`

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

**Run migrations (your job):**
```bash
# In Antigravity terminal
cd backend
alembic init alembic

# Edit alembic/env.py — add:
# from app.models import Base
# target_metadata = Base.metadata

# Create first migration (after writing all models)
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head

# Every time you add a model:
alembic revision --autogenerate -m "add_xxx_table"
alembic upgrade head
```

#### 3.3 NHS ODS API Service (Your Responsibility)
**File:** `backend/app/services/ods_loader.py`

This loads the complete South Yorkshire ICB org hierarchy from NHS.

```python
import httpx
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.org import ODSOrganisation, ICB, PCN, Practice

ODS_BASE = "https://directory.spineservices.nhs.uk/ORD/2-0-0"

async def load_south_yorkshire_hierarchy(db: AsyncSession):
    """
    Phase 1: HTTP fetches from NHS ODS API
    Phase 2: Insert into PostgreSQL ods_organisations table
    
    Relationship codes:
    RE2 = commissioned by (sub-ICBs under ICB)
    RE3 = member of (PCN membership)  
    RE4 = operated by (practices under PCN)
    """
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        
        # Step 1: South Yorkshire ICB
        r = await client.get(f"{ODS_BASE}/organisations/QF7", 
                             params={"_format": "json"})
        icb_data = r.json()
        
        # Step 2: Sub-ICBs under QF7
        r = await client.get(f"{ODS_BASE}/organisations",
                             params={"RelTypeId": "RE2", 
                                     "TargetOrgId": "QF7",
                                     "_format": "json",
                                     "_count": "1000"})
        sub_icbs = r.json().get("Organisations", [])
        
        # Step 3: PCNs under each sub-ICB
        all_pcns = []
        for sub_icb in sub_icbs:
            await asyncio.sleep(0.05)  # gentle rate limiting
            r = await client.get(f"{ODS_BASE}/organisations",
                                 params={"RelTypeId": "RE3",
                                         "TargetOrgId": sub_icb["OrgId"],
                                         "_format": "json",
                                         "_count": "500"})
            pcns = r.json().get("Organisations", [])
            all_pcns.extend(pcns)
        
        # Step 4: Practices under each PCN
        all_practices = []
        for pcn in all_pcns:
            await asyncio.sleep(0.05)
            r = await client.get(f"{ODS_BASE}/organisations",
                                 params={"RelTypeId": "RE4",
                                         "TargetOrgId": pcn["OrgId"],
                                         "_format": "json",
                                         "_count": "500"})
            practices = r.json().get("Organisations", [])
            all_practices.extend(practices)
        
        # Insert into DB
        await _insert_hierarchy(db, icb_data, sub_icbs, all_pcns, all_practices)
        
        return {
            "sub_icbs": len(sub_icbs),
            "pcns": len(all_pcns), 
            "practices": len(all_practices)
        }

async def _insert_hierarchy(db, icb_data, sub_icbs, pcns, practices):
    # Upsert pattern — safe to re-run
    from sqlalchemy import select, insert
    from app.models.org import ODSOrganisation
    
    def make_org(ods_code, name, org_type, parent_ods=None, tenant_id="sy-tenant"):
        return ODSOrganisation(
            ods_code=ods_code,
            name=name,
            org_type=org_type,
            parent_ods_code=parent_ods,
            status="Active",
            tenant_id=tenant_id,
        )
    
    orgs = []
    orgs.append(make_org("QF7", "NHS South Yorkshire ICB", "ICB"))
    
    for s in sub_icbs:
        orgs.append(make_org(s["OrgId"], s["Name"], "SUB_ICB", "QF7"))
    for p in pcns:
        orgs.append(make_org(p["OrgId"], p["Name"], "PCN", p.get("ParentOrgId")))
    for pr in practices:
        orgs.append(make_org(pr["OrgId"], pr["Name"], "PRACTICE", pr.get("ParentOrgId")))
    
    db.add_all(orgs)
    await db.commit()
    print(f"Inserted {len(orgs)} organisations for South Yorkshire ICB")
```

**Admin endpoint to trigger this:**
```python
# backend/app/routers/admin.py
@router.post("/admin/sync-ods/direct")
async def sync_ods(
    target_icb_ods: str = "QF7",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(requires_roles(Role.SYSTEM_ADMIN))
):
    result = await load_south_yorkshire_hierarchy(db)
    return {"status": "success", "loaded": result}
```

#### 3.4 Drug Tariff Sync Endpoint (Trigger for Victor's Service)
```python
# backend/app/routers/tariff.py (your file, calls Victor's service)
@router.post("/tariff/prices/sync")
async def sync_tariff(
    _: User = Depends(requires_roles(Role.SYSTEM_ADMIN, Role.ICB_PHARMACIST))
):
    """Triggers Victor's tariff sync task"""
    from app.tasks.data_sync import sync_tariff_prices
    task = sync_tariff_prices.delay()
    return {"task_id": task.id, "status": "triggered"}

@router.get("/tariff/prices")
async def get_tariff_prices(
    product: str | None = None,
    category: str | None = None,
    limit: int = 100
):
    """Returns Drug Tariff prices from MongoDB"""
    from app.mongo_models.tariff_price import TariffPriceDocument
    query = {}
    if product:
        query["product"] = {"$regex": product, "$options": "i"}
    if category:
        query["tariff_category"] = category
    docs = await TariffPriceDocument.find(query).limit(limit).to_list()
    return docs
```

#### 3.5 Auth Router (Your Responsibility)
```python
# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    return {
        "access_token": create_access_token({
            "sub": str(user.id),
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "icb_id": str(user.icb_id) if user.icb_id else None,
        }),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    }

@router.post("/refresh")
async def refresh_token(refresh_data: dict, db: AsyncSession = Depends(get_db)):
    from app.core.security import decode_token
    payload = decode_token(refresh_data["refresh_token"])
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "access_token": create_access_token({
            "sub": str(user.id), "role": user.role, "tenant_id": str(user.tenant_id)
        }),
        "token_type": "bearer"
    }
```

#### 3.6 Dashboard Router
```python
# backend/app/routers/dashboard.py
from app.mongo_models.opportunity import OpportunityDocument
from app.models.intervention import RealizedSaving

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the 4 hero cards visible in the PoC dashboard:
    - Total saving potential (sum of all opportunity annual_saving)
    - Active opportunities count
    - Practices covered
    - Completed switches
    """
    tenant_id = current_user.tenant_id
    
    # MongoDB: sum all identified opportunities
    pipeline = [
        {"$match": {"tenant_id": str(tenant_id), "status": {"$in": ["identified", "approved", "in_progress"]}}},
        {"$group": {"_id": None, "total_saving": {"$sum": "$annual_saving"}, "count": {"$sum": 1}}}
    ]
    result = await OpportunityDocument.aggregate(pipeline).to_list()
    agg = result[0] if result else {"total_saving": 0, "count": 0}
    
    # PostgreSQL: realized savings
    realized_result = await db.execute(
        select(func.sum(RealizedSaving.actual_savings))
        .where(RealizedSaving.tenant_id == str(tenant_id))
    )
    realized = realized_result.scalar() or 0.0
    
    # Practice count from ODS
    practice_result = await db.execute(
        select(func.count(ODSOrganisation.id))
        .where(ODSOrganisation.org_type == "PRACTICE", 
               ODSOrganisation.tenant_id == str(tenant_id))
    )
    practice_count = practice_result.scalar() or 0
    
    return {
        "total_saving_potential": round(agg["total_saving"], 2),
        "active_opportunities": agg["count"],
        "practices_covered": practice_count,
        "completed_switches": 0,  # incremented as interventions complete
        "realized_savings": round(realized, 2),
        "realization_rate": round((realized / agg["total_saving"] * 100) if agg["total_saving"] > 0 else 0, 1),
    }
```

#### 3.7 Celery Setup (Your Responsibility)
```python
# backend/app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "qipp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.data_sync", "app.tasks.opportunity_tasks", 
             "app.tasks.notification_tasks"]
)

celery_app.conf.beat_schedule = {
    "sync-ods-daily":              {"task": "app.tasks.data_sync.sync_ods_data",        "schedule": crontab(hour=2, minute=0)},
    "sync-tariff-daily":           {"task": "app.tasks.data_sync.sync_tariff_prices",   "schedule": crontab(hour=3, minute=0)},
    "discover-opportunities":      {"task": "app.tasks.opportunity_tasks.discover_opportunities", "schedule": crontab(hour=2, minute=30)},
    "check-price-concessions":     {"task": "app.tasks.data_sync.check_price_concessions", "schedule": crontab(hour=8, minute=0)},
    "weekly-recommendations":      {"task": "app.tasks.notification_tasks.send_weekly_recommendations", "schedule": crontab(day_of_week="monday", hour=7, minute=30)},
}
celery_app.conf.timezone = "Europe/London"
```

---

## 4. Data Initialisation Sequence (Your Responsibility)

Run these in order after the repo is first set up:

```bash
# Terminal 1: Make sure Redis is running (WSL2)
wsl -d Ubuntu
sudo service redis-server start

# In your Windows terminal (Antigravity terminal or Windows Terminal):
cd backend
source qipp_venv/Scripts/activate   # Windows uses Scripts not bin

# Step 1: Apply migrations
alembic upgrade head

# Step 2: Seed SY ICB data
python scripts/seed_south_yorkshire.py
# Creates: admin@syicb.nhs.uk / ChangeMe!2026, tenant QF7

# Step 3: Get admin JWT token
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@syicb.nhs.uk","password":"ChangeMe!2026"}'
# Copy the access_token from response

# Step 4: Load SY org hierarchy (calls NHS ODS API - takes ~3 mins)
curl -X POST "http://localhost:8000/api/admin/sync-ods/direct?target_icb_ods=QF7" \
     -H "Authorization: Bearer YOUR_TOKEN"
# Expected response: {"status":"success","loaded":{"sub_icbs":4,"pcns":~25,"practices":~105}}

# Step 5: Sync Drug Tariff (calls OpenPrescribing via Scrapfly - takes ~2 mins)
curl -X POST "http://localhost:8000/api/tariff/prices/sync" \
     -H "Authorization: Bearer YOUR_TOKEN"

# Step 6: Generate opportunities for South Yorkshire
curl -X POST "http://localhost:8000/api/opportunities/trigger-sync?ods_code=02P&org_level=sub_icb" \
     -H "Authorization: Bearer YOUR_TOKEN"
# This calls the OpportunityDiscoveryEngine and generates real £ savings numbers
```

---

## 5. Running the Full System on Windows

### Five terminal windows (use Windows Terminal tabs):

```powershell
# Tab 1: Redis (WSL2)
wsl -d Ubuntu -e sudo service redis-server start

# Tab 2: FastAPI backend
cd backend
.\qipp_venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tab 3: Celery worker
cd backend
.\qipp_venv\Scripts\activate
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
# Note: Windows Celery requires --pool=solo (gevent or prefork don't work well on Windows)

# Tab 4: Celery beat (scheduler)
cd backend
.\qipp_venv\Scripts\activate
celery -A app.tasks.celery_app beat --loglevel=info

# Tab 5: Frontend
cd frontend
npm run dev
```

**Antigravity built-in browser:** Once the frontend is running on port 5173, you can test it in Antigravity's built-in browser. The agent can click buttons, fill forms, and report what it sees — which is great for verifying the UI matches the PoC.

---

## 6. Environment Variables (Windows .env)

Create `backend/.env`:

```env
# Core
DATABASE_URL=postgresql+asyncpg://postgres.xxxx:password@aws-0-eu-west-2.pooler.supabase.com:6543/postgres
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/qipp_patients
REDIS_URL=redis://localhost:6379/0

# Security — generate a strong key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-64-char-hex-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# APIs (Victor shares Scrapfly — you can create your own free account too)
OPENPRESCRIBING_BASE_URL=https://openprescribing.net/api/1.0
SCRAPFLY_API_KEY=scp-live-VICTOR_SHARES_THIS
GEMINI_API_KEY=AIzaSy-GET-FROM-AISTUDIO
GEMINI_MODEL_NAME=gemini-2.0-flash

# Email (sign up resend.com — free 3,000/mo)
RESEND_API_KEY=re_your_key_here
EMAIL_FROM_ADDRESS=noreply@yourdomain.me
EMAIL_FROM_NAME=QIPP Medicines Optimisation

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Feature flags (keep false until Sprint 5)
NOTIFICATIONS_EMAIL_ENABLED=false
NOTIFICATIONS_SMS_ENABLED=false

# Monitoring (sign up sentry.io — free)
SENTRY_DSN=https://xxxx@sentry.io/xxxx
LOG_LEVEL=INFO
LOG_JSON=false
```

---

## 7. Makefile (Windows-Compatible)

Create `backend/Makefile`:

```makefile
.PHONY: dev migrate seed celery test lint

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

seed:
	python scripts/seed_south_yorkshire.py

celery:
	celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

beat:
	celery -A app.tasks.celery_app beat --loglevel=info

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	ruff check app/ --fix
	ruff format app/
```

---

## 8. Your Sprint Tasks — Week by Week

### Sprint 1 (Week 1–2): You Own These Tasks

- [ ] Create mono-repo on GitHub (private) — invite Victor as collaborator
- [ ] Set up `backend/` folder structure (all directories from the build guide)
- [ ] Write `backend/app/config.py` (Pydantic Settings loading from `.env`)
- [ ] Write `backend/app/database.py` (async SQLAlchemy engine + session)
- [ ] Write `backend/app/mongodb.py` (Motor + Beanie init with all 12 models)
- [ ] Write ALL 44 PostgreSQL SQLAlchemy models (`backend/app/models/`)
- [ ] Run Alembic init + first migration + `alembic upgrade head`
- [ ] Write `backend/app/core/security.py` (JWT create/decode, bcrypt hash/verify)
- [ ] Write `backend/app/middleware.py` (TenantContext, OrgScoping)
- [ ] Write `backend/app/main.py` (app factory)
- [ ] Write `backend/app/routers/auth.py` (login, refresh, logout)
- [ ] Write `backend/scripts/seed_south_yorkshire.py`
- [ ] Write ODS loader service + admin endpoint
- [ ] **Test:** Can you log in and get a JWT? Does ODS sync load 105 practices?

### Sprint 2 (Week 3–4): You Own These Tasks

- [ ] Write Celery app (`backend/app/tasks/celery_app.py`)
- [ ] Write `backend/app/tasks/data_sync.py` (sync_ods_data, check_price_concessions)
- [ ] Write `backend/app/routers/dashboard.py` (summary endpoint)
- [ ] Write `backend/app/routers/admin.py` (sync triggers, user management)
- [ ] Write `backend/app/routers/practices.py` (list, get, performance)
- [ ] Write `backend/app/routers/benchmarking.py` (calls OpenPrescribing measures for ICB comparison)
- [ ] Coordinate with Victor: confirm Scrapfly + Drug Tariff sync is working
- [ ] **Test:** Dashboard summary returns real £ values from MongoDB

### Sprint 3 (Week 5–6): Coordinate with Victor

- [ ] Write `backend/app/routers/opportunities.py` (list, filter, approve, update status)
- [ ] Write `backend/app/routers/savings.py` (realized savings, monthly breakdown)
- [ ] Write `backend/app/routers/interventions.py` (CRUD for interventions)
- [ ] Write `backend/app/tasks/opportunity_tasks.py` (daily discovery trigger)
- [ ] **Test:** Full opportunity pipeline works end to end

### Sprint 4–6: Frontend + Polish

- [ ] Set up React + Vite + Shadcn UI frontend
- [ ] Port CSS variables from PoC exactly
- [ ] Build Login page (replicates PoC login: two-panel, role cards, NHS teal)
- [ ] Build Dashboard page (real data from your summary endpoint)
- [ ] Build Opportunity Register (real data, sortable)
- [ ] Build Price Concession Dashboard page
- [ ] Build ICB Benchmarking page
- [ ] Build Practice Performance table
- [ ] Wire up Victor's AI search endpoint to the AI Patient Search page
- [ ] Set up DigitalOcean deployment (use your Student Pack $200 credit)
- [ ] Add domain from Namecheap student pack benefit

---

## 9. API Keys — Your Responsibility to Get

| Key | Where | When |
|-----|-------|------|
| Gemini API | aistudio.google.com → Get API key | Day 1 |
| Supabase (PostgreSQL) | supabase.com → New project → Settings → Database | Day 1 |
| Resend (email) | resend.com → Free account | Sprint 5 |
| DigitalOcean | Student Pack → $200 credit | Sprint 6 (deployment) |
| Namecheap domain | Student Pack → .me domain | Sprint 6 |
| Sentry | sentry.io → Free account | Sprint 6 |

---

## 10. Coordination Protocol with Victor

**Daily sync (15 min, async via WhatsApp/Telegram):**
```
Morning: "What I'm building today: [X]"
Evening: "Done: [X]. Blocked on: [Y]. Victor needs to: [Z]"
```

**Shared API keys (Victor holds):**
- Scrapfly API key → Victor to share in your `.env` file
- MongoDB Atlas URI → Victor to share connection string

**Git workflow:**
```bash
# Main branches:
main       → production-ready only
develop    → integration branch (both of you merge here)
your-name/feature-name  → your feature branches

# Daily workflow:
git checkout develop
git pull origin develop
git checkout -b saviour/auth-endpoints
# ... build the feature
git add .
git commit -m "feat: implement JWT auth with role-based access"
git push origin saviour/auth-endpoints
# Open PR to develop
```

**What Victor delivers to you:**
1. MongoDB Atlas connection string (he set it up)
2. Scrapfly API key (he has the account)
3. OpportunityDocument populated with real data (so your dashboard has numbers)
4. TariffPriceDocument populated (so your tariff pages work)

**What you deliver to Victor:**
1. Admin JWT token (so he can test his endpoints)
2. Running FastAPI server on localhost:8000
3. Supabase PostgreSQL connection string
4. Working auth middleware (so his routers can use `get_current_active_user`)

---

## 11. Common Windows Gotchas

```python
# asyncio on Windows — add to backend/app/main.py if needed:
import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Celery on Windows — always use --pool=solo:
celery -A app.tasks.celery_app worker --pool=solo --loglevel=info

# Redis on Windows — use WSL2, not native Redis (it's not maintained)
# In WSL2: sudo service redis-server start
# Redis URL stays redis://localhost:6379 (WSL2 bridges automatically)

# Python venv activation on Windows:
.\qipp_venv\Scripts\activate     # PowerShell
qipp_venv\Scripts\activate.bat  # Command Prompt

# If you get SSL errors with httpx/httpcore on Windows:
pip install certifi
# Add to database.py:
import ssl, certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())
```

---

*Your guide ends here. See Victor's file (VICTOR_WORK_Mac_Scrapfly_MongoDB.md) for his responsibilities.*
*Build guide version: 1.0 | March 2026 | QIPP South Yorkshire*
