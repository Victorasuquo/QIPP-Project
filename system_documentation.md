# QIPP Medicines Optimisation Automation System — System Documentation

> **Version:** 1.0  
> **Date:** March 2026  
> **Classification:** Internal Technical Reference  
> **Repository:** `Victorasuquo/QIPP-Medicines-Optimization-Automation-System`  
> **Branch:** `main`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Design](#4-database-design)
5. [External Integrations](#5-external-integrations)
6. [Authentication & Authorisation](#6-authentication--authorisation)
7. [NHS Organisation Hierarchy & Data Scoping](#7-nhs-organisation-hierarchy--data-scoping)
8. [Role-Based Access Control (RBAC)](#8-role-based-access-control-rbac)
9. [Dashboard System](#9-dashboard-system)
10. [Background Task Infrastructure](#10-background-task-infrastructure)
11. [AI Integration](#11-ai-integration)
12. [Clinical Safety & Governance](#12-clinical-safety--governance)
13. [Email & Notification System](#13-email--notification-system)
14. [PDF Generation](#14-pdf-generation)
15. [Frontend Architecture](#15-frontend-architecture)
16. [Environment Configuration](#16-environment-configuration)
17. [Deployment & Infrastructure](#17-deployment--infrastructure)
18. [How to Access the System](#18-how-to-access-the-system)
19. [API Reference](#19-api-reference)
20. [Data Flow Diagrams](#20-data-flow-diagrams)

---

## 1. Executive Summary

QIPP Medicines Optimisation is a **B2B healthcare SaaS platform** built for NHS Integrated Care Boards (ICBs). It automates the discovery, execution, and tracking of medication switching and deprescribing workflows across the full NHS commissioning hierarchy: **ICB → Sub-ICB → PCN → Practice**.

The system ingests live NHS data from OpenPrescribing and the Drug Tariff, identifies cost-saving opportunities where cheaper generic alternatives exist, generates action sheets for GP practices, tracks whether patients remain on the new medication or revert ("bounce-back"), and provides financial dashboards at every organisational level.

**Ref:** `CLAUDE.md` (project overview), `ARCHITECTURE.md` (data model & integration strategy)

---

## 2. System Architecture

### 2.1 High-Level Architecture

The system follows a **dual-database, event-driven microservice** design:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Server** | FastAPI (Python 3.11+) | REST API, WebSocket, application logic |
| **Relational DB** | PostgreSQL 16 (via Supabase) | Users, orgs, interventions, tenants, audit logs |
| **Document DB** | MongoDB Atlas | Patients, prescriptions, medications, tariff prices, opportunities, ICB reports |
| **Task Queue** | Celery + Redis | Background jobs (NHS data sync, reports, AI scoring) |
| **Cache / Broker** | Redis 7 | Celery message broker, result backend, rate limiting |
| **Frontend** | React 18 + TypeScript + Vite | Single-page application served on port 5173 |

**Ref:** `backend/app/main.py` (application factory `create_app()`), `backend/app/database.py` (PostgreSQL engine), `backend/app/mongodb.py` (MongoDB Atlas connection)

### 2.2 Application Factory Pattern

The FastAPI app is created via `create_app()` in `backend/app/main.py`. This function:
1. Registers exception handlers (custom `AppException` + generic 500 handler)
2. Sets up middleware stack (CORS, request ID, tenant context, org scoping, security headers, request logging)
3. Mounts **38 routers** under the `/api` prefix
4. Connects MongoDB Atlas on startup, disconnects on shutdown

**Ref:** `backend/app/main.py` lines 30–162

### 2.3 Middleware Stack

Five middleware layers execute on every request, in order:

| Order | Middleware | File | Purpose |
|-------|-----------|------|---------|
| 1 | `CORSMiddleware` | `backend/app/middleware.py` | Allows `localhost:3000` and `localhost:5173` origins |
| 2 | `request_id_middleware` | `backend/app/middleware.py` | Attaches UUID `X-Request-ID` header |
| 3 | `tenant_context_middleware` | `backend/app/middleware.py` | Extracts `tenant_id` from `X-Tenant-ID` header or JWT |
| 4 | `org_scoping_middleware` | `backend/app/middleware.py` | Reads `X-Org-Level` and `X-Org-ODS-Code` headers for data isolation |
| 5 | `security_headers_middleware` | `backend/app/middleware.py` | Adds `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, HSTS (prod) |
| 6 | `request_logging_middleware` | `backend/app/middleware.py` | Logs method, path, status, duration via structlog |

Public paths that bypass tenant/org resolution: `/health`, `/api/auth/login`, `/api/auth/refresh`, `/docs`, `/redoc`, `/openapi.json`.

**Ref:** `backend/app/middleware.py` lines 1–131

---

## 3. Technology Stack

### 3.1 Backend Dependencies

Declared in `backend/pyproject.toml`:

| Category | Package | Version | Purpose |
|----------|---------|---------|---------|
| **Framework** | FastAPI | ≥0.109.0 | Async REST API |
| **Server** | Uvicorn | ≥0.27.0 | ASGI server |
| **PostgreSQL** | SQLAlchemy 2.0 (async) | ≥2.0.25 | ORM, async sessions |
| **PostgreSQL Driver** | asyncpg | ≥0.29.0 | Async PostgreSQL wire protocol |
| **Migrations** | Alembic | ≥1.13.0 | Schema versioning |
| **MongoDB** | Motor | ≥3.3.2 | Async MongoDB driver |
| **MongoDB ODM** | Beanie | ≥1.24.0 | Document-object mapping |
| **Validation** | Pydantic 2 | ≥2.5.0 | Request/response schemas |
| **Settings** | pydantic-settings | ≥2.1.0 | `.env` file loading |
| **Auth** | python-jose | ≥3.3.0 | JWT encoding/decoding |
| **Password** | passlib + bcrypt | ≥1.7.4 | Bcrypt hashing (12 rounds) |
| **Task Queue** | Celery | ≥5.3.6 | Distributed background tasks |
| **Redis** | redis-py | ≥5.0.1 | Celery broker + result backend |
| **HTTP Client** | httpx | ≥0.27.0 | NHS ODS API, OpenPrescribing |
| **Scraping** | Scrapfly SDK | — | Cloudflare bypass for OpenPrescribing |
| **AI** | google-genai | ≥0.8.0 | Gemini 2.0 Flash (clinical search, recommendations) |
| **Email (Primary)** | Resend | ≥2.0.0 | Transactional email |
| **Email (Fallback)** | aiosmtplib | ≥3.0.0 | SMTP fallback |
| **PII Encryption** | cryptography | ≥42.0.0 | AES-256-GCM for Zone 3 data |
| **PDF** | WeasyPrint | ≥61.0 | Action sheet & patient letter PDFs |
| **Data Processing** | Pandas | ≥2.1.0 | CSV/tariff parsing |
| **Logging** | structlog | ≥24.1.0 | Structured JSON logging |
| **Monitoring** | Sentry SDK | ≥1.40.0 | Error tracking |

**Ref:** `backend/pyproject.toml` lines 13–85

### 3.2 Frontend Dependencies

Declared in `health-guard-pro/package.json`:

| Category | Package | Purpose |
|----------|---------|---------|
| **Framework** | React 18 | UI library |
| **Language** | TypeScript | Type-safe JavaScript |
| **Bundler** | Vite | Dev server + HMR + build |
| **Routing** | react-router-dom 6 | Client-side routing |
| **State** | TanStack Query 5 | Server state management, caching, invalidation |
| **UI Components** | Radix UI primitives + shadcn/ui | Accessible component library |
| **Styling** | TailwindCSS | Utility-first CSS |
| **Charts** | Recharts | Dashboard visualisations |
| **HTTP Client** | Axios | API requests with interceptors |
| **Forms** | react-hook-form + zod | Form validation |

**Ref:** `health-guard-pro/package.json` lines 16–89

---

## 4. Database Design

### 4.1 PostgreSQL (Relational — via Supabase)

PostgreSQL hosts the structured, transactional data. Connection is via `asyncpg` with connection pooling (5 pool size, 10 overflow, 300s recycle for Supabase idle connection handling).

**Connection string format:** `postgresql+asyncpg://<user>:<password>@<host>:5432/<db>`

**Ref:** `backend/app/database.py` lines 10–25, `backend/app/config.py` line 20

#### Core Tables

| Table | Model File | Purpose | Key Columns |
|-------|-----------|---------|-------------|
| `icbs` | `models/icb.py` | 47 NHS Integrated Care Boards | `name`, `ods_code`, `email_domain`, `prescribing_budget` |
| `pcns` | `models/pcn.py` | 1,299 Primary Care Networks | `name`, `ods_code`, `icb_id`, `sub_icb_ods_code`, `email_domain` |
| `practices` | `models/practice.py` | 7,680 GP practices | `name`, `ods_code`, `pcn_id`, `icb_id`, `sub_icb_ods_code`, `clinical_system`, `email_domain` |
| `users` | `models/user.py` | System users (auto-created from email) | `email`, `role`, `icb_id`, `practice_ods_code`, `pcn_ods_codes`, `sub_icb_ods_code`, `org_level`, `org_ods_code` |
| `tenants` | `models/tenant.py` | ICB-level tenant isolation | `name`, `ods_code`, `short_code`, `feature_flags`, `scoring_weights` |
| `interventions` | `models/intervention.py` | Medication switching workstreams | `name`, `current_drug`, `target_drug`, `status`, `practice_ods_codes` (JSONB), `forecast_annual_savings`, `realized_savings` |
| `action_sheets` | `models/action_sheet.py` | Generated clinical action documents | `workstream`, `icb_id`, `practice_ods_code`, `status`, `content` (JSONB) |
| `patient_worklist_items` | `models/patient_worklist.py` | Per-patient switch tracking | `practice_ods_code`, `nhs_number`, `status`, `current_drug`, `target_drug` |
| `patient_letters` | `models/patient_letter.py` | Patient notification letters | `practice_ods_code`, `nhs_number`, `email_sent`, `pdf_generated` |
| `realized_savings_monthly` | `models/realized_saving_monthly.py` | Monthly savings aggregation | `practice_ods_code`, `pcn_ods_code`, `period` (YYYY-MM), `realized_saving` |
| `org_email_domains` | `models/org_email_domain.py` | 9,136 email domain → org lookup entries | `email_domain`, `org_level`, `ods_code`, `org_name`, `icb_ods_code` |
| `audit_logs` | `models/audit_log.py` | Immutable audit trail | `user_id`, `action`, `resource_type`, `details` |
| `pii_patients` | `models/pii_patient.py` | AES-256-GCM encrypted patient PII (Zone 3) | `nhs_number`, `encrypted_name`, `encrypted_dob` |
| `notifications` | `models/notification.py` | In-app notification queue | `user_id`, `event_type`, `channel`, `sent_at` |
| `patent_expiries` | `models/patent_expiry.py` | Drug patent expiry monitoring | `drug_name`, `patent_expiry_date`, `generic_available` |
| `formulary_entries` | `models/formulary.py` | ICB-specific preferred drug lists | `tenant_id`, `bnf_code`, `preferred_status` |
| `switching_rules` | `models/switching_rule.py` | Clinical switching criteria | `current_drug_bnf`, `target_drug_bnf`, `exclusion_criteria` |
| `prescribing_data` | `models/prescribing_data.py` | OpenPrescribing spending data | `practice_id`, `bnf_code`, `items`, `actual_cost` |

**Ref:** `backend/app/models/__init__.py`, individual model files in `backend/app/models/`

#### Alembic Migrations

Schema migrations are managed via Alembic. Migration files are in `backend/alembic/versions/`. Key migrations include:

- `a46432b971ab` — Initial schema (users, ICBs, practices, interventions)
- `a1b2c3d4e5f6` — Add `sub_icb_ods_code` to practices and PCNs
- `b2c3d4e5f6g7` — Add `org_email_domains` table and user org fields
- `d6d22fc97af9` — Add hierarchical scopes to users (`org_level`, `org_ods_code`, `org_name`)
- `c3d4e5f6g7h8` — Add `practice_ods_code` to action_sheets

**Ref:** `backend/alembic/versions/`, `backend/alembic.ini`

### 4.2 MongoDB Atlas (Document Store)

MongoDB hosts the flexible clinical and pricing data that changes shape frequently. Connection is via Motor (async driver) with Beanie ODM.

**Connection string format:** `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority`  
**Database name:** `qipp_patients` (configurable via `MONGODB_DB_NAME`)

**Ref:** `backend/app/mongodb.py` lines 1–90, `backend/app/config.py` lines 23–24

#### Document Collections

| Collection | Model File | Purpose | Key Fields |
|-----------|-----------|---------|------------|
| `patients` | `models/patient_mongo.py` → `PatientDocument` | Rich clinical patient records | `nhs_number`, `practice_ods_code`, `medications[]`, `conditions[]`, `allergies[]`, `risk_level`, `switch_status`, `estimated_annual_savings` |
| `prescriptions` | `models/patient_mongo.py` → `PrescriptionDocument` | Prescription event history | `patient_nhs_number`, `bnf_code`, `prescriber_ods` |
| `patient_analytics` | `models/patient_mongo.py` → `PatientAnalyticsDocument` | Per-patient savings analytics | `patient_nhs_number`, `actual_realized_savings` |
| `practice_measures` | `models/patient_mongo.py` → `PracticeMeasureDocument` | OpenPrescribing measure data per practice | `practice_ods_code`, `measure_id` |
| `opportunities` | `models/opportunity_mongo.py` → `OpportunityDocument` | Cost-saving opportunities at all 4 hierarchy levels | `org_level`, `practice_ods_code`, `pcn_ods_code`, `sub_icb_ods_code`, `icb_id`, `workstream`, `estimated_annual_savings`, `effort_reward_score` |
| `medications` | `models/medication_mongo.py` → `MedicationDocument` | BNF drug catalog (15-char BNF codes) | `bnf_code`, `name`, `is_generic`, `workstream`, `cost_per_unit` |
| `drug_classes` | `models/medication_mongo.py` → `DrugClassDocument` | BNF hierarchy (chapter → section → paragraph) | `bnf_id`, `name`, `level`, `parent_id` |
| `tariff_prices` | `models/tariff_mongo.py` → `TariffPriceDocument` | NHS Drug Tariff pricing (500,000+ rows monthly) | `vmpp_id`, `vmpp`, `price_pence`, `tariff_category`, `date`, `concession` |
| `tariff_sync_logs` | `models/tariff_mongo.py` → `TariffSyncLogDocument` | Tariff sync audit trail | `status`, `records_fetched`, `records_stored` |
| `icb_monthly_reports` | `models/icb_report_mongo.py` → `ICBReportDocument` | Auto-generated monthly ICB performance reports | `icb_id`, `month`, `year`, `total_theoretical_savings`, `total_realized_savings`, `practice_breakdown[]` |
| `sync_logs` | `models/patient_mongo.py` → `SyncLogDocument` | Data sync operation history | `source`, `records_processed`, `errors` |

**Ref:** `backend/app/mongodb.py` → `connect_mongodb()` function registers all 12 document models with Beanie

### 4.3 Redis (Cache + Message Broker)

Redis serves three roles via different database numbers:

| DB | URL | Purpose |
|----|-----|---------|
| 0 | `redis://localhost:6379/0` | Application cache, rate limiting |
| 1 | `redis://localhost:6379/1` | Celery task broker |
| 2 | `redis://localhost:6379/2` | Celery result backend |

**Ref:** `backend/app/config.py` lines 27–39

---

## 5. External Integrations

### 5.1 OpenPrescribing.net (via Scrapfly)

The primary source of NHS prescribing data. OpenPrescribing is protected by Cloudflare Turnstile, so all requests route through **Scrapfly's headless browser API** (`asp=True` for anti-bot bypass).

**Service:** `backend/app/services/openprescribing_service.py` → `OpenPrescribingService`

**How it works:**
1. Check if a local cached file exists in `backend/data/scrapfly_cache/` and is fresh (< 24 hours old)
2. If stale/missing → send request via Scrapfly SDK with Cloudflare bypass
3. Save raw response to disk cache
4. Parse JSON/CSV and return structured data

**Endpoints consumed:**

| Endpoint | Purpose | Schedule |
|----------|---------|----------|
| `GET /api/1.0/bnf_code/?q={CODE}` | BNF drug catalog lookup | Weekly via Celery |
| `GET /api/1.0/spending_by_org/?org={ODS}` | Practice-level prescribing spend | Every 30 min via Celery |
| `GET /api/1.0/tariff/?format=csv` | Full Drug Tariff (500K+ rows) | 1st of month at 08:00 UTC |
| `GET /api/1.0/measure/` | Prescribing measures & outliers | Daily at 02:00 UTC |

**QIPP Workstream BNF Mappings:**

| Workstream | BNF Prefix | Drug Class |
|-----------|-----------|------------|
| DPP4 | `0601022` | Dipeptidylpeptidase-4 inhibitors |
| SGLT2 | `0601023` | SGLT-2 inhibitors |
| STATINS | `0212000` | Lipid-regulating drugs |
| ACE | `0205051` | ACE inhibitors |
| BETA_BLOCKERS | `0204000` | Beta-adrenoceptor blocking drugs |

**Configuration:**
- `SCRAPFLY_API_KEY` — Required for live data fetching (set in `.env`)
- `SCRAPFLY_DATA_DIR` — Local cache directory (default: `./data/scrapfly_cache`)

**Ref:** `backend/app/services/openprescribing_service.py` lines 1–80, `ARCHITECTURE.md` §2

### 5.2 NHS ODS API

The Organisation Data Service API provides authoritative organisational data for all NHS bodies.

**Service:** `backend/app/services/ods_service.py`  
**Schedule:** Weekly sync on Sunday 02:00 UTC via `backend/app/tasks/ods_sync_tasks.py`  
**Populates:** ICBs, Sub-ICBs (via practice `sub_icb_ods_code`), PCNs, Practices with addresses, postcodes, phone numbers

**Ref:** `backend/app/services/ods_service.py`, `backend/app/tasks/ods_sync_tasks.py`

### 5.3 ePACT2 (NHS Business Services Authority)

Authorised access to detailed prescribing data (more granular than OpenPrescribing). Requires client credentials.

**Configuration:**
- `EPACT2_CLIENT_ID`
- `EPACT2_CLIENT_SECRET`
- `EPACT2_BASE_URL`

**Ref:** `backend/app/config.py` lines 101–103, `backend/app/services/epact_service.py`

### 5.4 GOV.UK Notify

NHS-approved email and SMS service for patient/clinician communications.

**Configuration:** 6 template IDs for different notification types:
- `GOVUK_NOTIFY_TEMPLATE_OPPORTUNITY_APPROVED`
- `GOVUK_NOTIFY_TEMPLATE_WORKSTREAM_ASSIGNED`
- `GOVUK_NOTIFY_TEMPLATE_SWITCHBACK_DETECTED`
- `GOVUK_NOTIFY_TEMPLATE_WEEKLY_RECOMMENDATION`
- `GOVUK_NOTIFY_TEMPLATE_LETTER_SENT`
- `GOVUK_NOTIFY_TEMPLATE_PRICE_ALERT`

**Ref:** `backend/app/config.py` lines 94–100

### 5.5 Clinical System Webhooks (EMIS / SystmOne)

The system exposes a webhook endpoint for real-time prescription events from GP clinical systems.

**Endpoint:** `POST /api/webhooks/clinical/prescription_event`  
**Auth:** `X-Webhook-Token` header  
**Purpose:** Detects "bounce-back" events — when a patient reverts to an expensive brand after being switched to a generic

**Bounce-back detection flow:**
1. Webhook receives `{nhs_number, bnf_code, practice_ods_code}`
2. Looks up patient in MongoDB by `nhs_number`
3. If `switch_status == SWITCHED` and the new `bnf_code` matches the original expensive drug → flag as `BOUNCED_BACK`
4. Deduct the lost savings from practice/ICB analytics totals
5. Push alert to the practice notifications tab

**Ref:** `backend/app/routers/webhooks.py` lines 1–84, `ARCHITECTURE.md` §4

### 5.6 GP Connect (FHIR)

Service for reading patient records from GP clinical systems via the NHS GP Connect API.

**Ref:** `backend/app/services/gp_connect_service.py`

---

## 6. Authentication & Authorisation

### 6.1 Login Flow (Zero Pre-Registration)

The system uses **email-domain auto-scoping** — no pre-created user accounts needed. Any NHS staff member logs in with their organisational email, and the system auto-detects their NHS hierarchy level.

**Flow:**
```
User enters email + password
    → POST /api/auth/login
    → AuthService.login() looks up user by email
    → If user exists: update last_login, issue JWT
    → If user does NOT exist:
        → OrgResolutionService.resolve_from_email()
            → Parse email domain (e.g. "barnsley.pcn.nhs.uk")
            → Look up domain in org_email_domains table (9,136 entries)
            → Resolve full hierarchy (Practice → PCN → Sub-ICB → ICB)
            → Determine role from org_level
        → Auto-create user with correct scoping fields
        → Issue JWT
```

**Important:** The password field exists on the login form but the backend **does not verify passwords**. Any string ≥ 6 characters is accepted. This is a deliberate design choice for the development phase.

**Ref:** `backend/app/services/auth_service.py` lines 52–130, `backend/app/services/org_resolution_service.py`

### 6.2 JWT Token Structure

Tokens are signed with HS256. Two token types are issued:

| Token | Expiry | Contains |
|-------|--------|----------|
| Access Token | 30 minutes | `sub` (user UUID), `role`, `icb_id`, `org_level`, `org_ods_code`, `type: "access"` |
| Refresh Token | 7 days | Same claims + `type: "refresh"` |

**Ref:** `backend/app/core/security.py` lines 30–55

### 6.3 Token Validation Chain

```
HTTP Request with Bearer token
    → HTTPBearer extracts token
    → get_current_user() decodes JWT, loads User from DB
    → get_current_active_user() checks is_active == True
    → RoleChecker / TenantScopedRoleChecker validates role
    → get_practice_scope() / get_pcn_scope() enforces data boundaries
```

**Ref:** `backend/app/dependencies.py` lines 22–80

### 6.4 Organisation Resolution Service

Converts email domains to NHS organisations with full hierarchy.

**Service:** `backend/app/services/org_resolution_service.py` → `OrgResolutionService`

**Resolution strategy:**
1. **Exact match** — look up `email_domain` in `org_email_domains` table
2. **Fuzzy fallback** — extract keywords from domain, search org names
3. **No match** → return `None` (login rejected with "Could not identify your organisation")

**Hierarchy resolution:** Given an org level + ODS code, resolves the complete chain:
- Practice → look up PCN, Sub-ICB, ICB
- PCN → look up Sub-ICB, ICB
- Sub-ICB → look up ICB
- ICB → top level

**Ref:** `backend/app/services/org_resolution_service.py` lines 1–228

### 6.5 Email Domain Generation

The script `backend/generate_email_domains.py` auto-generates email domains for all 9,136 organisations in the database:

| Org Level | Pattern | Example |
|-----------|---------|---------|
| Practice | `{sanitised_name}.surgery.nhs.uk` | `tennantstreet.surgery.nhs.uk` |
| PCN | `{sanitised_name}.pcn.nhs.uk` | `barnsley.pcn.nhs.uk` |
| Sub-ICB | `{ods_code}.ccg.nhs.uk` | `02P.ccg.nhs.uk` |
| ICB | `{abbreviation}.icb.nhs.uk` | `bsol.icb.nhs.uk` |

**Stop words removed:** `the`, `and`, `of`, `nhs`, `icb`, `pcn`, `medical`, `practice`, `surgery`, `group`, `centre`, `center`, `health`, `care`, `primary`, `network`, `integrated`, `board`, `sub`, `location`, `gp`

**Ref:** `backend/generate_email_domains.py` lines 1–204

---

## 7. NHS Organisation Hierarchy & Data Scoping

### 7.1 Hierarchy Model

The NHS is structured in four levels. The database contains:

| Level | Count | Table | Identifier |
|-------|-------|-------|-----------|
| **ICB** (Integrated Care Board) | 47 | `icbs` | UUID `id` + `ods_code` (e.g. `QHL`) |
| **Sub-ICB** (former CCG) | 106 | No dedicated table; stored as `sub_icb_ods_code` on practices and PCNs | ODS code (e.g. `02P`) |
| **PCN** (Primary Care Network) | 1,299 | `pcns` | UUID `id` + `ods_code` (e.g. `U16464`) |
| **Practice** (GP Surgery) | 7,680 | `practices` | UUID `id` + `ods_code` (e.g. `A81006`) |

**Hierarchy chain:** Practice `→ pcn_id →` PCN `→ icb_id →` ICB. Sub-ICB is stored as `sub_icb_ods_code` on both practices and PCNs.

6,129 practices have the full chain (ICB + Sub-ICB + PCN) populated.

**Ref:** `levels.md` (current state table), `backend/app/models/practice.py`, `backend/app/models/pcn.py`, `backend/app/models/icb.py`

### 7.2 Data Scoping Rules

Every API endpoint enforces data boundaries based on the user's `org_level`:

| User Level | Sees Data For | Enforced By |
|-----------|--------------|-------------|
| ICB | All practices/PCNs under their ICB | `user.icb_id` match |
| Sub-ICB | All practices/PCNs under their Sub-ICB ODS code | `user.sub_icb_ods_code` match |
| PCN | Only practices within their PCN | `user.pcn_ods_codes` array |
| Practice | Only their own practice | `user.practice_ods_code` match |

Scoping is enforced at two layers:
1. **Frontend:** Axios interceptor attaches `X-Org-Level` and `X-Org-ODS-Code` headers from `localStorage`
2. **Backend:** `org_scoping_middleware` injects these into `request.state`, and role-specific endpoint handlers verify them

**Ref:** `backend/app/core/permissions.py` → `get_practice_scope()`, `get_pcn_scope()`, `backend/app/middleware.py` → `org_scoping_middleware`, `health-guard-pro/src/api/axios.ts` lines 20–27

---

## 8. Role-Based Access Control (RBAC)

### 8.1 Role Taxonomy

| Role | Auto-Assigned When | Scope |
|------|--------------------|-------|
| `admin` / `system_admin` | Seeded manually | Full system access |
| `icb_pharmacist` | Email matches `*.icb.nhs.uk` | ICB-wide, all zones |
| `icb_leader` | Seeded (executive) | ICB-wide, read-only |
| `sub_icb_lead` | Email matches `*.ccg.nhs.uk` | Sub-ICB scoped |
| `pcn_pharmacist` | Email matches `*.pcn.nhs.uk` | PCN-only, all clinical zones |
| `practice_pharmacist` | Email matches `*.surgery.nhs.uk` | Single practice |
| `pharmacy_technician` | Seeded (same scope as practice) | Single practice |

**Ref:** `backend/app/services/auth_service.py` lines 26–30 (`_LEVEL_TO_ROLE` mapping)

### 8.2 Data Zone Access

Three data classification zones control what each role can see:

| Zone | Contains | Accessible By |
|------|----------|--------------|
| **Zone 1** (Aggregated) | ICB-level savings, workstream totals, trend data | All roles |
| **Zone 2** (Practice-level) | Per-practice spend, PCN comparisons, outlier analysis | ICB roles, Sub-ICB lead, PCN pharmacist |
| **Zone 3** (Patient PII) | NHS number, patient name, DOB, clinical records | Admin, ICB pharmacist, PCN pharmacist, practice staff |

Zone access is checked via `check_zone_access(user, zone)` which raises 403 if denied.

**Ref:** `backend/app/core/permissions.py` lines 57–67 (`ROLE_PERMISSIONS` matrix)

### 8.3 Feature Access Matrix

Each role has access to specific features:

| Role | Features |
|------|----------|
| `admin` | `*` (all) |
| `icb_pharmacist` | dashboard, formulary, search, interventions, action_sheets, patients |
| `icb_leader` | dashboard, reports, interventions |
| `pcn_pharmacist` | dashboard, search, interventions, action_sheets, patients |
| `practice_pharmacist` | dashboard, search, action_sheets, patients |
| `gp` | dashboard, patients |

**Ref:** `backend/app/core/permissions.py` lines 57–67, `health-guard-pro/src/lib/roleGuard.ts` (frontend route matrix)

### 8.4 Pre-Built Dependency Checkers

| Checker | Roles Allowed |
|---------|--------------|
| `require_admin` | admin, system_admin |
| `require_pharmacist_or_above` | admin, system_admin, pharmacist, icb_pharmacist, pcn_pharmacist, practice_pharmacist |
| `require_clinical_staff` | All clinical roles |
| `require_any_role` | All authenticated users |
| `require_icb_manager` | ICB-level roles only |
| `require_leadership` | Admin, ICB manager, ICB leader, Sub-ICB lead |

**Ref:** `backend/app/core/permissions.py` lines 200–220

---

## 9. Dashboard System

### 9.1 Backend Dashboard Endpoints

The `dashboard_analytics.py` router (1,194 lines) implements four role-based dashboards:

**§8.1 ICB Leadership Dashboard** (`/api/dashboards/icb-leadership/*`)
- `GET /savings-by-workstream` — Realized savings per workstream
- `GET /forecast-vs-actual` — Forecast vs actual savings comparison
- `GET /time-series` — Monthly savings trend data
- `GET /practice-drill-down` — Per-practice breakdown
- `GET /csv-export` — Full data export as CSV

**§8.2 ICB Pharmacist Dashboard** (`/api/dashboards/icb-pharmacist/*`)
- `GET /opportunity-pipeline` — Active opportunities by stage
- `GET /spend-outliers` — Practices spending above peers
- `GET /savings-trajectory` — Projected savings over time
- `GET /worklist-rates` — Switch completion rates

**§8.3 PCN Pharmacist Dashboard** (`/api/dashboards/pcn/{pcn_ods}/*`)
- `GET /overview` — PCN-scoped financial summary
- `GET /workstreams` — Active workstreams in the PCN
- `GET /switch-progress` — Patient switching progress
- `GET /switchback-alerts` — Patients who reverted

**§8.4 Practice Staff Dashboard** (`/api/dashboards/practice/{practice_ods}/*`)
- `GET /action-sheets` — Assigned action sheets for the practice
- `GET /worklist` — Patient worklist with completion rate
- `GET /switchback-alerts` — Practice-level switchback alerts
- `GET /letters` — Patient letter send status

**§8.5 Sub-ICB Dashboard** (`/api/dashboards/sub-icb/{sub_icb_ods}/*`)
- `GET /overview` — Sub-ICB financial summary with PCN/practice counts
- `GET /workstreams` — Active workstreams across the Sub-ICB
- `GET /practice-performance` — Per-practice performance within the Sub-ICB

**Ref:** `backend/app/routers/dashboard_analytics.py` lines 1–1194

### 9.2 Frontend Dashboard Pages

| Page | File | Route | Role |
|------|------|-------|------|
| ICB Leadership | `ICBLeadershipDashboard.tsx` | `/dashboard/icb-leadership` | `icb_leader` |
| ICB Pharmacist | `ICBPharmacistDashboard.tsx` | `/dashboard/icb-pharmacist` | `icb_pharmacist` |
| Sub-ICB | `SubICBDashboard.tsx` | `/dashboard/sub-icb` | `sub_icb_lead` |
| PCN Pharmacist | `PCNPharmacistDashboard.tsx` | `/dashboard/pcn-dashboard` | `pcn_pharmacist` |
| Practice Staff | `PracticeStaffDashboard.tsx` | `/dashboard/practice-dashboard` | `practice_pharmacist`, `pharmacy_technician` |

**Auto-routing:** After login, `roleGuard.ts` → `getDefaultRoute(role)` redirects the user to their correct dashboard.

**Ref:** `health-guard-pro/src/pages/`, `health-guard-pro/src/lib/roleGuard.ts`

---

## 10. Background Task Infrastructure

### 10.1 Celery Configuration

Celery is configured with JSON serialisation, UTC timezone, and task acknowledgement after completion (`task_acks_late = True`).

**Task queues:**

| Queue | Tasks |
|-------|-------|
| `patient_sync` | Patient data sync (every 30 min), patient analytics compute (every 35 min) |
| `medication_sync` | Medication catalog sync (every 30 min) |
| `pricing` | Monthly tariff refresh (1st of month 08:00), mid-month concession check (15th) |
| `reports` | Monthly ICB reports (1st of month 09:00), tariff diff alerts (1st 10:00) |
| `ai` | Weekly recommendations (Mon 06:00), daily switchback scan (03:00), supply risk refresh (04:00) |
| `notifications` | Weekly email digests (Mon 07:00), event-driven notifications |
| `celery` | Opportunity discovery (daily 02:00), re-rank after tariff refresh (1st 09:00), MongoDB→PG sync (daily 01:00) |
| `background` | Patent expiry scan (1st of month 06:00) |

**Ref:** `backend/app/tasks/celery_app.py` lines 1–148

### 10.2 Task Files

| File | Tasks |
|------|-------|
| `patient_tasks.py` | `sync_patient_data`, `compute_patient_analytics` |
| `medication_tasks.py` | `sync_medications_data_task` |
| `pricing_tasks.py` | `refresh_drug_tariff_prices`, `check_price_concessions` |
| `reporting_tasks.py` | `generate_monthly_reports_task`, `run_tariff_diff_and_alert_task` |
| `recommendation_tasks.py` | `generate_weekly_recommendations` |
| `switchback_tasks.py` | `scan_for_switchbacks` |
| `supply_risk_tasks.py` | `refresh_supply_risk_data` |
| `email_digest_tasks.py` | `send_weekly_email_digests` |
| `notification_tasks.py` | `send_notification_task` |
| `ods_sync_tasks.py` | `sync_ods_data` (weekly ODS hierarchy refresh) |
| `patent_monitoring_tasks.py` | `scan_for_patent_expiries` |
| `mongo_sync_tasks.py` | `sync_opportunities` (MongoDB → PostgreSQL) |
| `public_data_tasks.py` | Public data refresh |

**Ref:** `backend/app/tasks/` directory

---

## 11. AI Integration

### 11.1 Google Gemini (Primary AI)

The system uses **Google Gemini 2.0 Flash** for clinical intelligence features.

**Client:** `backend/app/ai/client.py` → Singleton `genai.Client` with lazy initialisation  
**Model:** Configurable via `GEMINI_MODEL_NAME` (default: `gemini-2.0-flash`)  
**Temperature:** 0.2 (low for clinical accuracy)  
**Max tokens:** 8,192

**AI features:**
- Clinical search query building (natural language → structured drug search)
- Weekly prescribing recommendations
- Opportunity scoring assistance
- Action sheet content generation

**Ref:** `backend/app/ai/client.py` lines 1–78

### 11.2 AI Safety Guardrails

All AI output passes through `validate_ai_output()` before reaching users. This enforces:

**Blocked phrases** (imperative autonomous actions):
- Dose manipulation: "change the dose", "increase the dose", "titrate the dose"
- Stopping therapy: "stop the medication", "discontinue the medication"
- Autonomous actions: "override the clinician", "automatically switch", "prescribe immediately"

**Mandatory disclaimer** appended to all AI output:
> ⚠️ AI-GENERATED — Clinician Review Required. This output was generated by an AI assistant and must be reviewed and approved by a qualified pharmacist or clinician before any action is taken.

**Ref:** `backend/app/ai/guardrails.py` lines 1–104

### 11.3 AI Audit Trail

All AI-generated decisions are logged in `ai_decision_audits` table for DCB0129 compliance, recording:
- Input prompt
- Raw AI output
- Post-guardrail output
- Confidence score
- Clinician approval status

**Ref:** `backend/app/models/ai_decision_audit.py`, `backend/app/routers/governance.py` → AI confidence scoring endpoints

---

## 12. Clinical Safety & Governance

### 12.1 Compliance Frameworks

The governance module (`backend/app/routers/governance.py`, 837 lines) implements:

| Standard | Coverage |
|----------|----------|
| **UK GDPR** | DPIA document, lawful basis (Article 6(1)(e) — public task), PII auto-purge, right-of-access endpoints |
| **DCB0129** | Clinical Safety Case Report, hazard log, CSO configuration |
| **DCB0160** | Clinical risk management for health IT |
| **DSPT** | Data Security and Protection Toolkit compliance checklist |
| **DTAC** | Digital Technology Assessment Criteria |

**Ref:** `backend/app/routers/governance.py` lines 1–80 (DPIA document structure)

### 12.2 PII Encryption (Zone 3)

Patient Personally Identifiable Information is encrypted at rest using **AES-256-GCM**:
- Encryption key: 256-bit key from `PII_ENCRYPTION_KEY` env var (dev fallback: SHA-256 of a static string)
- Nonce: 12-byte random per field
- Storage format: Base64-encoded `nonce + ciphertext`
- Every PII access is logged in `PIIAccessLog` with user ID, timestamp, and action

**Ref:** `backend/app/services/pii_service.py` lines 1–60

### 12.3 Audit Trail

Immutable audit log captures all significant actions:
- User ID, action type, resource type, resource ID
- Request IP, user agent
- Before/after state diffs for mutations
- Exported via CSV for compliance reviews

**Ref:** `backend/app/models/audit_log.py`, `backend/app/core/audit.py`

---

## 13. Email & Notification System

### 13.1 Email Delivery

The email system uses a **primary + fallback** architecture:

| Priority | Provider | Config Key | Purpose |
|----------|----------|-----------|---------|
| 1 (Primary) | **Resend** | `RESEND_API_KEY` | Modern transactional email API |
| 2 (Fallback) | **SMTP** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Traditional SMTP relay |

If Resend fails, the system automatically falls back to SMTP. If both fail, the error is raised.

**Ref:** `backend/app/email/sender.py` lines 1–60

### 13.2 Notification Channels

| Channel | Provider | Config |
|---------|----------|--------|
| In-app | PostgreSQL `notifications` table | Always enabled |
| Email | Resend → SMTP fallback | `NOTIFICATIONS_EMAIL_ENABLED` |
| SMS | Twilio | `NOTIFICATIONS_SMS_ENABLED`, `TWILIO_ACCOUNT_SID` |
| GOV.UK Notify | NHS-approved service | `GOVUK_NOTIFY_API_KEY` |

### 13.3 Notification Event Types

- Opportunity approved
- Workstream assigned
- Switchback detected
- Weekly recommendation digest
- Patient letter sent
- Drug price alert

**Ref:** `backend/app/services/notifications/`, `backend/app/tasks/notification_tasks.py`

---

## 14. PDF Generation

The system generates two types of PDF documents using **WeasyPrint** + **Jinja2** templates:

| Document | Generator | Template Dir | Purpose |
|----------|----------|-------------|---------|
| **Action Sheets** | `backend/app/pdf/action_sheet_pdf.py` | `templates/action_sheets/` | Clinical switching instructions for GP practices |
| **Patient Letters** | `backend/app/pdf/patient_letter_pdf.py` | `templates/letters/` | Patient notification letters about medication changes |

Additional template directories: `templates/emails/` (email bodies), `templates/reports/` (ICB monthly reports)

**Ref:** `backend/app/pdf/` directory

---

## 15. Frontend Architecture

### 15.1 Project Structure

```
health-guard-pro/
├── src/
│   ├── api/           # 31 API client modules (one per backend router)
│   ├── components/    # Shared UI components (AppLayout, ProtectedRoute, ErrorBoundary)
│   ├── hooks/         # Custom React hooks (useAuth, useDashboard, useTariff, etc.)
│   ├── lib/           # roleGuard.ts (RBAC routing), utils.ts
│   ├── pages/         # 43 page components (lazy-loaded)
│   ├── data/          # Static data files
│   └── App.tsx        # Route definitions, QueryClient, providers
```

### 15.2 API Client Layer

Each API module in `src/api/` corresponds to a backend router. The shared Axios instance (`src/api/axios.ts`) provides:
- **Base URL:** `http://localhost:8000` (configurable via `VITE_API_BASE_URL`)
- **Auth interceptor:** Attaches `Bearer {access_token}` from localStorage
- **Org scoping interceptor:** Attaches `X-Org-Level` and `X-Org-ODS-Code` headers
- **401 handler:** Auto-redirect to `/login` on token expiry

**Ref:** `health-guard-pro/src/api/axios.ts` lines 1–68

### 15.3 Auth Hook

`useAuth()` provides:
- `user` — Current `UserProfile` (includes org hierarchy)
- `isAuthenticated` — Boolean auth state
- `login(credentials)` — Calls `POST /api/auth/login`, stores tokens, fetches profile
- `logout()` — Clears tokens and org scoping from localStorage

On login, the hook persists `org_level` and `org_ods_code` to localStorage for the Axios interceptor.

**Ref:** `health-guard-pro/src/hooks/useAuth.ts` lines 1–83

### 15.4 Route Protection

`<ProtectedRoute>` wraps all authenticated routes. `roleGuard.ts` maps roles to allowed routes and provides `getDefaultRoute(role)` for post-login redirect:

| Role | Default Route |
|------|--------------|
| `admin` | `/dashboard` |
| `icb_pharmacist` | `/dashboard/icb-pharmacist` |
| `icb_leader` | `/dashboard/icb-leadership` |
| `sub_icb_lead` | `/dashboard/sub-icb` |
| `pcn_pharmacist` | `/dashboard/pcn-dashboard` |
| `practice_pharmacist` | `/dashboard/practice-dashboard` |
| `pharmacy_technician` | `/dashboard/practice-dashboard` |

**Ref:** `health-guard-pro/src/lib/roleGuard.ts` lines 1–168

---

## 16. Environment Configuration

All configuration is loaded from `backend/.env` via pydantic-settings. Below is every configuration variable:

### 16.1 Application

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | "QIPP Medicines Optimization" | Application name |
| `APP_ENV` | "development" | Environment (development / production) |
| `DEBUG` | `True` | Enable debug mode (Swagger UI, echo SQL) |
| `API_PREFIX` | "/api" | API route prefix |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | Allowed CORS origins |

### 16.2 Databases

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://qipp_user:qipp_password@localhost:5432/qipp_db` | PostgreSQL connection (Supabase in production) |
| `MONGODB_URI` | `mongodb+srv://...` | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | `qipp_patients` | MongoDB database name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |

### 16.3 Authentication

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET_KEY` | (must change) | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |

### 16.4 Background Tasks

| Variable | Default | Purpose |
|----------|---------|---------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery result store |

### 16.5 External Services

| Variable | Purpose |
|----------|---------|
| `SCRAPFLY_API_KEY` | Cloudflare bypass for OpenPrescribing |
| `GEMINI_API_KEY` | Google Gemini AI |
| `RESEND_API_KEY` | Resend email service |
| `SENDGRID_API_KEY` | SendGrid notifications |
| `GOVUK_NOTIFY_API_KEY` | GOV.UK Notify (NHS email/SMS) |
| `EPACT2_CLIENT_ID` / `EPACT2_CLIENT_SECRET` | ePACT2 prescribing data |
| `PII_ENCRYPTION_KEY` | AES-256 key for Zone 3 PII (hex string) |
| `SENTRY_DSN` | Error monitoring |

**Ref:** `backend/app/config.py` lines 1–123

---

## 17. Deployment & Infrastructure

### 17.1 Docker Compose (Local Development)

`backend/docker-compose.yml` defines four services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `db` | postgres:16-alpine | 5433:5432 | Local PostgreSQL |
| `redis` | redis:7-alpine | 6379:6379 | Cache + Celery broker |
| `app` | Custom Dockerfile | 8000:8000 | FastAPI application |
| `celery-worker` | Same Dockerfile | — | Background task processor |

**Ref:** `backend/docker-compose.yml` lines 1–80

### 17.2 Production Stack

| Component | Service | Notes |
|-----------|---------|-------|
| PostgreSQL | **Supabase** | Managed PostgreSQL with `pool_recycle=300` to handle idle kills |
| MongoDB | **MongoDB Atlas** | Cloud document store |
| Redis | Self-hosted or managed | Required for Celery |
| Backend | Uvicorn behind reverse proxy | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Frontend | **Vercel** | Static React build (see `health-guard-pro/vercel.json`) |

### 17.3 Startup Sequence

```bash
# 1. Start Redis
redis-server &

# 2. Start Celery worker
cd backend && source quid_venv/bin/activate
celery -A app.tasks.celery_app worker -l info -Q medication_sync,celery

# 3. Apply migrations
alembic upgrade head

# 4. Seed database (first run only)
python -m app.seed

# 5. Generate email domains (first run only)
python generate_email_domains.py

# 6. Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Start frontend (separate terminal)
cd health-guard-pro && npm run dev
```

**Ref:** `notes.txt`, `backend/Makefile`

---

## 18. How to Access the System

### 18.1 URLs

| Service | URL |
|---------|-----|
| **Backend API** | `http://localhost:8000` |
| **Swagger UI** | `http://localhost:8000/api/docs` |
| **ReDoc** | `http://localhost:8000/api/redoc` |
| **Frontend** | `http://localhost:5173` |

### 18.2 Seeded Users

These 6 users are created by `python -m app.seed`:

| Role | Email | Password | Scope |
|------|-------|----------|-------|
| System Admin | `admin@qipp.nhs.uk` | `changeme123!` | Full access |
| ICB Pharmacist | `icb.pharmacist@bsol.icb.nhs.uk` | `IcbPharmacist1!` | NHS Birmingham & Solihull ICB |
| ICB Leader | `icb.leader@bsol.icb.nhs.uk` | `IcbLeader1!` | NHS Birmingham & Solihull ICB (read-only) |
| PCN Pharmacist | `pcn.pharmacist@boldmere.pcn.nhs.uk` | `PcnPharmacist1!` | North Birmingham PCN |
| Practice Pharmacist | `practice.pharmacist@boldmere.surgery.nhs.uk` | `PracticePharm1!` | Shah Zaman Surgery (M85001) |
| Pharmacy Technician | `technician@boldmere.surgery.nhs.uk` | `Technician1!` | Shah Zaman Surgery (M85001) |

**Note:** Password is not verified — any 6+ character string works for login.

### 18.3 Login as Any NHS Organisation

No pre-registration needed. Use any email matching an organisation's domain:

**ICB login examples (47 available):**

| ICB | Domain | Example Login |
|-----|--------|--------------|
| NHS South Yorkshire | `southyorkshire.icb.nhs.uk` | `anyone@southyorkshire.icb.nhs.uk` |
| NHS Birmingham & Solihull | `bsol.icb.nhs.uk` | `anyone@bsol.icb.nhs.uk` |

**Sub-ICB login examples (106 available):**

| Sub-ICB | Domain | Example Login |
|---------|--------|--------------|
| Barnsley (02P) | `02P.ccg.nhs.uk` | `anyone@02P.ccg.nhs.uk` |
| Doncaster (02X) | `02X.ccg.nhs.uk` | `anyone@02X.ccg.nhs.uk` |

**PCN login examples (1,299 available):**

| PCN | Domain | Example Login |
|-----|--------|--------------|
| Barnsley PCN (U16464) | `barnsley.pcn.nhs.uk` | `anyone@barnsley.pcn.nhs.uk` |

**Practice login examples (7,680 available):**

| Practice | Domain | Example Login |
|----------|--------|--------------|
| Royston Group Practice | `royston.surgery.nhs.uk` | `anyone@royston.surgery.nhs.uk` |

**Ref:** `notes.txt` (login credentials), `levels.md` (auto-scoping flow)

---

## 19. API Reference

### 19.1 Router Summary

The backend mounts **38 routers**, all under `/api`:

| Router | Prefix | File | Purpose |
|--------|--------|------|---------|
| Health | `/health` | `routers/health.py` | Liveness/readiness probes |
| Auth | `/api/auth` | `routers/auth.py` | Login, logout, refresh, profile (`/me`) |
| Users | `/api/users` | `routers/users.py` | User CRUD |
| Dashboard | `/api/dashboard` | `routers/dashboard.py` | Legacy dashboard |
| Dashboard Analytics | `/api/dashboards` | `routers/dashboard_analytics.py` | 4 role-based dashboards (§8.1–8.4) |
| Data Import | `/api/data-import` | `routers/data_import.py` | CSV/Excel upload |
| Patients | `/api/patients` | `routers/patients.py` | Patient list, search, detail |
| Opportunities | `/api/opportunities` | `routers/opportunities.py` | Opportunity pipeline |
| Action Sheets | `/api/action-sheets` | `routers/action_sheets.py` | Action sheet CRUD + PDF |
| Reports | `/api/reports` | `routers/reports.py` | ICB monthly reports |
| Medications | `/api/medications` | `routers/medications.py` | Drug catalog |
| Switching Rules | `/api/switching-rules` | `routers/switching_rules.py` | Clinical switching criteria |
| Practices | `/api/practices` | `routers/practices.py` | Practice lookup |
| Notifications | `/api/notifications` | `routers/notifications.py` | Notification queue |
| Tariff | `/api/tariff` | `routers/tariff.py` | Drug Tariff search |
| Savings | `/api/savings` | `routers/savings.py` | Realized savings tracking |
| Webhooks | `/api/webhooks` | `routers/webhooks.py` | EHR prescription events |
| ICB Analytics | `/api/icb-analytics` | `routers/icb_analytics.py` | ICB-level analytics |
| Verification | `/api/verification` | `routers/verification.py` | Ground-truth verification |
| Tenants | `/api/tenants` | `routers/tenants.py` | Multi-tenant management |
| Formulary | `/api/formulary` | `routers/formulary.py` | ICB formulary CRUD |
| Interventions | `/api/interventions` | `routers/interventions.py` | Intervention lifecycle |
| Clinical Search | `/api/clinical-search` | `routers/clinical_search.py` | AI-powered drug search |
| Rebates | `/api/rebates` | `routers/rebates.py` | Pharmaceutical rebate tracking |
| ODS Hierarchy | `/api/ods` | `routers/ods_hierarchy.py` | NHS org hierarchy browser |
| Users Management | `/api/users-management` | `routers/users_management.py` | Admin user management |
| Data Freshness | `/api/data-freshness` | `routers/data_freshness.py` | Data sync status |
| Public Data | `/api/public-data` | `routers/public_data.py` | Public prescribing data |
| Tenant Analytics | `/api/tenant-analytics` | `routers/tenant_analytics.py` | Per-tenant analytics |
| Pricing | `/api/pricing` | `routers/pricing.py` | 3-stage pricing engine |
| Integration | `/api/integration` | `routers/integration.py` | External system connections |
| Worklist | `/api/worklist` | `routers/worklist.py` | Patient worklist management |
| Governance | `/api/governance` | `routers/governance.py` | DPIA, audit, compliance (§9–10) |
| Clinical Extensions | `/api/clinical-extensions` | `routers/clinical_extensions.py` | Care home, SNOMED, medication history (§14–18) |
| Admin | `/api/admin` | `routers/admin.py` | ODS sync, system operations |
| Patent Expiry | `/api/patent-expiry` | `routers/patent_expiry.py` | Generic launch monitoring |

### 19.2 Key API Endpoints

**Authentication:**
- `POST /api/auth/login` — Login (auto-creates user from email domain)
- `POST /api/auth/refresh` — Refresh access token
- `GET /api/auth/me` — Current user profile with hierarchy

**Opportunities:**
- `GET /api/opportunities` — List opportunities (filtered by user scope)
- `GET /api/opportunities/{id}` — Opportunity detail with pricing

**Interventions:**
- `POST /api/interventions` — Create new intervention
- `PUT /api/interventions/{id}/status` — Advance lifecycle (DRAFT → APPROVED → IN_EXECUTION → COMPLETED)

**Webhooks:**
- `POST /api/webhooks/clinical/prescription_event` — EHR prescription event (bounce-back detection)

**Ref:** Full OpenAPI spec available at `http://localhost:8000/api/docs`

---

## 20. Data Flow Diagrams

### 20.1 Opportunity Discovery Pipeline

```
OpenPrescribing API → Scrapfly (Cloudflare bypass) → Local file cache
    → Parse JSON/CSV
    → Cross-reference with Drug Tariff prices (MongoDB: tariff_prices)
    → Identify expensive → cheap switches
    → Score via ScoringEngine (6-factor weighted composite)
    → Rank and de-duplicate
    → Store in MongoDB: opportunities collection
    → Sync to PostgreSQL: interventions table (daily at 01:00 UTC)
```

**Ref:** `backend/app/services/opportunity_discovery.py`, `backend/app/services/scoring_engine.py`

### 20.2 Scoring Engine Formula

Each opportunity is scored using a 6-factor weighted composite:

$$\text{score} = w_1(\text{cash}) + w_2(\text{certainty}) + w_3(\text{cohort}) + w_4(\text{suitability}) - w_5(\text{supply\_risk}) + w_6(\text{switchability})$$

| Factor | Weight | Source |
|--------|--------|--------|
| Cash value (£ annual saving) | 0.30 | Drug Tariff price differential |
| Certainty (tariff stability) | 0.15 | Historical price variance |
| Cohort size (patients affected) | 0.15 | OpenPrescribing item counts |
| Clinical suitability | 0.15 | Formulary alignment (1.0 if aligned, 0.4 if not) |
| Supply risk | 0.10 | Stock shortage probability (subtracted) |
| Switchability | 0.15 | Historical switch success rate |

Composite score is clamped to [0, 1] and classified into tiers:
- **high_value** — cash > 0.7 AND composite > 0.65
- **quick_win** — switchability > 0.7 AND supply_risk < 0.3
- **balanced** — everything else

**Ref:** `backend/app/services/scoring_engine.py` lines 1–146

### 20.3 3-Stage Pricing Engine

| Stage | Data Source | Latency | Purpose |
|-------|-----------|---------|---------|
| **Stage 1: Discovery** | OpenPrescribing benchmark data | ~2 months old | Initial opportunity sizing |
| **Stage 2: Decision** | Live Drug Tariff + concessions | Current month | Board-level approval |
| **Stage 3: Realized** | Actual prescribing post-switch | Real-time | Financial reporting |

Each stage produces scenario savings at 100%, 80%, and 50% switch rates.

**Ref:** `backend/app/services/pricing_engine.py` lines 1–160

### 20.4 Bounce-Back Detection Flow

```
GP prescribes drug for patient
    → EMIS/SystmOne sends webhook
    → POST /api/webhooks/clinical/prescription_event
    → Look up patient in MongoDB (by NHS number)
    → If patient.switch_status == SWITCHED:
        → Check if new BNF code matches original expensive drug
        → If match: flag BOUNCED_BACK
            → Wipe patient's realized_savings to £0
            → Deduct from practice/ICB analytics totals
            → Push alert to practice notifications
    → Return financial impact to webhook caller
```

**Ref:** `backend/app/routers/webhooks.py` lines 25–84, `ARCHITECTURE.md` §4

### 20.5 Monthly Drug Tariff Refresh

```
1st of month, 08:00 UTC → Celery task: refresh_drug_tariff_prices
    → Scrapfly fetches /api/1.0/tariff/?format=csv (500,000+ rows)
    → Parse CSV → TariffPriceDocument (MongoDB)
    → Overwrite tariff_prices collection with new month's data
    → 09:00 UTC → rerank_after_tariff_refresh
        → Recalculate all opportunity savings with new prices
        → Re-score and re-rank all opportunities
    → 10:00 UTC → run_tariff_diff_and_alert_task
        → Compare old vs new prices
        → Send price change alerts to relevant users
```

**Ref:** `backend/app/tasks/celery_app.py` (beat schedule), `backend/app/tasks/pricing_tasks.py`

---

## Appendix A: File Structure Summary

```
backend/
├── app/
│   ├── ai/                  # Gemini AI client, guardrails, prompt templates
│   ├── core/                # security.py, permissions.py, audit.py
│   ├── email/               # Resend + SMTP email clients
│   ├── models/              # 40 SQLAlchemy + Beanie models
│   ├── pdf/                 # WeasyPrint PDF generators
│   ├── repositories/        # Data access layer
│   ├── routers/             # 38 FastAPI router files
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # 35 business logic services
│   ├── tasks/               # 16 Celery task files
│   ├── templates/           # Jinja2 templates (action sheets, emails, letters, reports)
│   ├── config.py            # All env vars via pydantic-settings
│   ├── database.py          # Async SQLAlchemy engine
│   ├── dependencies.py      # Auth, tenant, scoping dependencies
│   ├── main.py              # Application factory
│   ├── middleware.py         # 5 middleware layers
│   ├── mongodb.py           # Motor + Beanie init
│   └── seed.py              # Demo data seeder
├── alembic/                 # Database migrations
├── tests/                   # pytest test suite
├── docker-compose.yml       # Local dev infrastructure
├── Makefile                 # Common commands
└── pyproject.toml           # Python dependencies

health-guard-pro/
├── src/
│   ├── api/                 # 31 API client modules
│   ├── components/          # Shared React components
│   ├── hooks/               # 9 custom hooks
│   ├── lib/                 # roleGuard.ts, utils.ts
│   └── pages/               # 43 page components
├── package.json             # Node dependencies
├── vite.config.ts           # Vite build config
└── vercel.json              # Vercel deployment config
```

---

## Appendix B: Database Record Counts (Current State)

| Entity | Count |
|--------|-------|
| ICBs | 47 |
| Distinct Sub-ICB ODS codes | 106 |
| PCNs | 1,299 |
| Practices | 7,680 |
| Practices with full hierarchy chain | 6,129 |
| Email domain lookup entries | 9,136 |
| Seeded users | 6 |

**Ref:** `levels.md` (current state table)

---

## Appendix C: Intervention Lifecycle State Machine

```
DRAFT → APPROVED → IN_EXECUTION → COMPLETED
                                 → PAUSED → IN_EXECUTION (resume)
                                 → ABANDONED
```

Each state transition is recorded in `state_history` (JSONB array on the `interventions` table) with `{state, reason, changed_by, timestamp}`.

**Ref:** `backend/app/models/intervention.py` lines 42–87

---

*Document generated from codebase analysis. All file references are relative to the repository root.*
