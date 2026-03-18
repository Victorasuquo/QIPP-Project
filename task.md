# QIPP — Full Build Checklist

> **You build everything on this machine.** Victor (macOS) owns: Scrapfly, OpenPrescribing data pipelines, OpportunityDiscoveryEngine, and AI layer. You own: all FastAPI backend + all React frontend.
>
> **Key shortcut:** The database already exists from V1. No migrations needed. Connect to existing Supabase + MongoDB and build the API layer on top.

---

## ✅ PHASE 0 — Environment Setup ✅ DONE

- [x] Create `backend/` folder inside `qippsystem/`
- [x] Create Python virtual environment: `python -m venv qipp_venv`
- [x] Install all Python dependencies ([requirements.txt](file:///c:/Users/testing/Documents/qippsystem/backend/requirements.txt)) — 78 packages
- [x] Verify connection to Supabase (PostgreSQL) ✅ 9,191 orgs, 47 ICBs confirmed
- [x] Verify connection to MongoDB Atlas ✅ 1,198 opportunities, 590,817 tariff prices confirmed
- [x] Verify Redis is running locally (WSL2 or Docker) ✅ `redis-server` listening on `localhost:6379`
- [x] Create `frontend/` folder
- [x] Scaffold React+Vite app: `npm create vite@latest . -- --template react-ts`
- [x] Install frontend dependencies (TanStack Query, Recharts, Shadcn UI, react-router-dom)

---

## 🔧 PHASE 1 — Backend Core ✅ DONE

- [x] [backend/app/config.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/config.py) — Pydantic Settings
- [x] [backend/app/database.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/database.py) — Async SQLAlchemy engine
- [x] [backend/app/mongodb.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/mongodb.py) — Motor + Beanie init (12 collections)
- [x] [backend/app/main.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/main.py) — FastAPI app factory + middleware + routers ✅ server running
- [x] [backend/app/middleware.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/middleware.py) — TenantContext + OrgScoping + SecurityHeaders
- [x] [backend/app/dependencies.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/dependencies.py) — [get_current_user](file:///c:/Users/testing/Documents/qippsystem/backend/app/dependencies.py#13-30), [get_tenant_id](file:///c:/Users/testing/Documents/qippsystem/backend/app/dependencies.py#39-42)
- [x] [backend/app/core/security.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/core/security.py) — bcrypt + JWT
- [x] [backend/app/core/permissions.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/core/permissions.py) — 13 roles + [requires_roles()](file:///c:/Users/testing/Documents/qippsystem/backend/app/core/permissions.py#39-52)
- [x] [backend/app/models/org.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/org.py) — 6 tables (icbs, pcns, practices, ods_organisations, tenants, org_email_domains)
- [x] [backend/app/models/user.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/user.py) — 2 tables (users, audit_logs)
- [x] [backend/app/models/clinical.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/clinical.py) — 7 tables
- [x] [backend/app/models/intervention.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/intervention.py) — 4 tables
- [x] [backend/app/models/ai.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/ai.py) — 3 tables
- [x] [backend/app/models/notification.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/notification.py) — 3 tables
- [x] [backend/app/models/data.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/models/data.py) — 9 tables → **44 tables total** ✅
- [x] All 9 MongoDB Beanie models written
- [x] [backend/app/schemas/auth.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/schemas/auth.py) + [common.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/schemas/common.py) — all Pydantic schemas
- [x] [backend/app/routers/auth.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/routers/auth.py) — `/login`, `/refresh`, `/me`, `/logout`
- [x] [backend/app/tasks/celery_app.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/tasks/celery_app.py) + 3 task stubs
- [x] **Phase 1 Test Gate PASSED** — server up, `/health` 200 OK, MongoDB connected

---

## 📊 PHASE 2 — Core API Endpoints ✅ DONE

- [x] `GET /api/dashboard/summary` — **£6,690,504** saving potential, 1,198 opps, 168 practices ✅
- [x] `GET /api/opportunities/` + `/{id}` + `/summary` + `PATCH /{id}/status` ✅
- [x] `GET /api/practices/` + `/{ods_code}` + `/search` + `/{ods_code}/opportunities` ✅
- [x] `GET /api/interventions/` + `/{id}` + `PATCH /{id}/status` ✅
- [x] `GET /api/savings/summary` + `/monthly` ✅
- [x] `GET /api/admin/users` + `GET /admin/health/db` + `POST /admin/sync-ods/direct` ✅
- [x] **Phase 2 Test Gate PASSED** — Dashboard returns real £ data, 1,198 real opportunities ✅

---

## 🤖 PHASE 3 — AI & Document Generation (Sprint 3, Week 5–6)

### AI Patient Search (Gemini)
- [x] `backend/app/services/gemini_service.py` — Gemini 2.5 Flash wrapper
- [x] `POST /api/ai-search/clinical-query` — plain English → EMIS/SystmOne query
- [x] `POST /api/ai-search/find-opportunities` — free-text opportunity discovery
- [x] `GET /api/ai-search/suggestions` — pre-built example queries

### Action Sheets & Letters
- [x] `POST /api/documents/action-sheet` — generate practice action sheet (Gemini)
- [x] `POST /api/documents/patient-letter` — generate patient letter
- [x] `POST /api/documents/sms` — generate SMS text
- [x] `GET /api/documents/{id}` — fetch previously generated document

### Notifications
- [x] `GET /api/notifications/` — unread in-app notifications
- [x] `PATCH /api/notifications/{id}/read` — mark as read
- [x] `POST /api/notifications/send-email` — trigger email via SendGrid

### ✅ Phase 3 Test Gate
- [x] AI search returns structured EMIS/SystmOne query for a sample DPP4 query
- [x] Action sheet generates real NHS-formatted document for an existing opportunity

---

## 🎨 PHASE 4 — React Frontend (Sprint 4, Week 7–9)

> Current mode: UI parity first (PoC-matched screens with static template data), then swap to live API data.

### Foundation
- [x] Copy all CSS variables from PoC HTML exactly (teal theme, dark gradients)
- [x] Set up `api/` client layer (Axios + TanStack Query)
- [x] Set up React Router with role-based route guards
- [x] Set up auth context (JWT storage, refresh, logout)

### Login Page
- [x] Two-panel layout (teal gradient left, form right) — matches PoC pixel-perfect
- [x] Role selector cards (GP Practice, PCN Pharmacist, ICB Pharmacist, Senior Leadership)
- [x] JWT login + error handling

### Dashboard
- [x] 4 hero metric cards (Saving Potential, Active Opportunities, Practices, Completed Switches) — live data
- [ ] Workstream summary table
- [ ] Recent activity feed

### PoC UI Parity Pass (March 2026)
- [x] Extract PoC datasets into frontend template data files (`pocData.ts`, `slData.ts`) for deterministic screen parity
- [x] Build role dashboards/tabs to mirror PoC information architecture (Senior, ICB, PCN, GP)
- [x] Implement sticky/frozen shell behavior for top bar + tab navigation
- [x] Refactor Top 5 / Bottom 5 practice rows to boxed PoC-style layout
- [x] Fix CSS scope regression (moved shared utility styles out of media-only block)
- [x] Add `frontend/vercel.json` SPA rewrites for client-side routing
- [x] Update backend CORS to allow localhost dynamic ports and Vercel app domains

### Opportunities Pages
- [ ] Opportunity register table (sortable: drug switch, workstream, saving, patients, ease score)
- [ ] Opportunity detail modal (exclusion criteria, clinical guidance, EMIS query)
- [ ] Status update flow (approve/reject)

### Financial Performance
- [ ] Expenditure by workstream chart (Recharts)
- [ ] Savings delivered vs target chart
- [ ] Top switches by value ranking

### ICB Benchmarking
- [x] SY vs comparator ICB metrics (PoC-style template UI)
- [ ] Live OpenPrescribing measure charts

### Practice Performance
- [ ] All 105 SY practices table with RAG status, savings YTD, switches progress bar

### AI Patient Search Page
- [ ] Example query chip buttons
- [ ] Free-text textarea → API call → structured EMIS/SystmOne result cards

### Find Opportunities Page (Claude/Gemini AI)
- [ ] Free-text query → Gemini API → opportunity cards with BNF codes, exclusions, savings

### Action Sheets & Letters Page
- [ ] Step 1: Select opportunity
- [ ] Step 2: Choose document type (action sheet / patient letter / SMS)
- [ ] Step 3: Preview + Print/Download/Share

### Switch Log
- [ ] Audit table with EPD verification status

### ✅ Phase 4 Test Gate
- [ ] Full login → dashboard → opportunity detail → generate action sheet flow works end-to-end in browser
- [ ] All numbers match what's in the existing database (not hardcoded)
- [ ] All remaining tabs are fully production-wired (AI search, Find my own opportunities, Documents, Switch log)

---

## ⚙️ PHASE 5 — Background Tasks & Data Refresh (Sprint 5)

- [ ] [backend/app/tasks/data_sync.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/tasks/data_sync.py) — ODS sync, tariff sync, concessions check
- [ ] [backend/app/tasks/opportunity_tasks.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/tasks/opportunity_tasks.py) — daily discovery trigger (calls Victor's engine)
- [ ] [backend/app/tasks/notification_tasks.py](file:///c:/Users/testing/Documents/qippsystem/backend/app/tasks/notification_tasks.py) — weekly recommendations email
- [ ] Start Celery worker + beat and confirm scheduled tasks fire correctly

---

## 🚀 PHASE 6 — Deployment (Sprint 6)

- [ ] Dockerfile for FastAPI backend
- [ ] `docker-compose.yml` (backend + Redis)
- [ ] Deploy backend to DigitalOcean (Student Pack $200 credit)
- [ ] Deploy frontend to Vercel or DigitalOcean App Platform
- [x] Add Vercel SPA routing config (`frontend/vercel.json`)
- [ ] Configure domain (Namecheap student pack)
- [ ] Set production environment variables
- [ ] Smoke test all endpoints on production URL

---

## 📋 Reference: Who Owns What

| Area | Owner |
|------|-------|
| FastAPI backend (all routers, models, schemas) | **You** |
| React frontend (all pages, components) | **You** |
| PostgreSQL models (SQLAlchemy) | **You** |
| MongoDB Beanie models | **You** (matches Victor's Atlas schema) |
| Celery app config + task shells | **You** |
| OpenPrescribing service + Scrapfly | **Victor** |
| OpportunityDiscoveryEngine | **Victor** |
| Gemini AI clinical search service | **Victor** |
| Drug Tariff sync task (implementation) | **Victor** |
| MongoDB Atlas cluster admin | **Victor** |
