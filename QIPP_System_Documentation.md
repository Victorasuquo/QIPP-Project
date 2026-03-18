# QIPP Medicines Optimization — Comprehensive System Documentation

> **Version:** 1.0 | **Last Updated:** 2026-03-15
> **Purpose:** Complete technical reference for the QIPP Medicines Optimization platform — architecture, data models, external API integrations, background tasks, authentication, and operational details.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Multi-Tenancy & RBAC](#3-multi-tenancy--rbac)
4. [Database Design](#4-database-design)
   - 4.1 PostgreSQL Models
   - 4.2 MongoDB Document Models
5. [Pydantic Schemas](#5-pydantic-schemas)
6. [External API Integrations](#6-external-api-integrations)
   - 6.1 OpenPrescribing API
   - 6.2 NHS ODS API
   - 6.3 Google Gemini AI API
   - 6.4 Scrapfly API
   - 6.5 NHS Drug Tariff (NHSBSA)
   - 6.6 GOV.UK Notify API
   - 6.7 Resend Email API
   - 6.8 Twilio SMS API
   - 6.9 SMTP Email (Fallback)
   - 6.10 ePACT2 (NHS BSA)
   - 6.11 NHS Digital dm+d
   - 6.12 GP Connect (FHIR R4)
7. [Background Tasks (Celery)](#7-background-tasks-celery)
8. [Middleware Stack](#8-middleware-stack)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Configuration Reference](#10-configuration-reference)
11. [Key Services](#11-key-services)
12. [Deployment & Operations](#12-deployment--operations)
13. [BNF Code System — Complete Reference](#13-bnf-code-system--complete-reference)
   - 13.1 BNF Code Structure & Hierarchy
   - 13.2 How the System Decomposes BNF Codes
   - 13.3 BNF Prefix Matching — The Core Pattern
   - 13.4 QIPP Workstream → BNF Code Mappings (5 mappings)
   - 13.5 BNF Codes in Opportunity Discovery — Full Algorithm
   - 13.6 BNF Codes in MongoDB Storage
   - 13.7 BNF Code Validation
   - 13.8 BNF Codes in Clinical Safety — Medication History Checks
   - 13.9 BNF Codes in Drug Tariff Price Lookups
   - 13.10 BNF Codes in Spending Data Enrichment
   - 13.11 BNF Codes in CSV Import & Bulk Loading
   - 13.12 BNF Codes in the Frontend
   - 13.13 BNF Code Quick Reference — All Codes Used in QIPP
   - 13.14 Summary: BNF Code Usage Across the System

---

## 1. System Overview

QIPP Medicines Optimization is a **B2B healthcare SaaS platform** built for NHS Integrated Care Boards (ICBs). It automates medication switching and deprescribing workflows by:

- **Discovering** cost-saving opportunities from NHS prescribing data (OpenPrescribing)
- **Ranking** opportunities using a composite scoring engine (cash value, certainty, cohort size, clinical suitability, supply risk, switchability)
- **Generating** action sheets and patient letters for GP practices
- **Tracking** realized savings across the full NHS hierarchy: ICB → Sub-ICB → PCN → Practice
- **Providing** AI-powered clinical search translation (plain English → EMIS/SystmOne queries)
- **Monitoring** drug tariff prices, patent expiries, and price concessions

### Key Statistics

| Metric | Count |
|--------|-------|
| External API integrations | 12 |
| PostgreSQL tables | 44 |
| MongoDB collections | 12 |
| Pydantic schemas | 80+ |
| Backend routers | 37 |
| API endpoints | 200+ |
| Frontend pages | 44 |
| Celery background tasks | 28+ |
| User roles | 13 |
| QIPP workstreams | 10 |

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Shadcn UI |
| **PostgreSQL** | Async SQLAlchemy 2.0, Alembic migrations |
| **MongoDB** | Motor (async driver), Beanie ODM |
| **Task Queue** | Celery 5 + Redis |
| **AI** | Google Gemini 2.0 Flash via `google-genai` SDK |
| **Web Scraping** | Scrapfly (Cloudflare bypass for OpenPrescribing) |
| **Email** | Resend API (primary), SMTP (fallback), GOV.UK Notify (NHS-approved) |
| **SMS** | Twilio |
| **Monitoring** | Structlog (structured JSON logging), Sentry, OpenTelemetry |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React 18 + Vite Frontend                    │
│  (TanStack Query, Shadcn UI, Recharts, react-router-dom)       │
│  Port 5173 (dev) — 31 API client modules, 44 pages             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS (JWT Bearer)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)                   │
│  37 routers under /api prefix                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Middleware Stack:                                           ││
│  │  CORS → RequestID → TenantContext → OrgScoping →           ││
│  │  RequestLogging → SecurityHeaders                          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │ Auth/RBAC  │  │ Dependencies │  │ Exception Handlers       ││
│  │ JWT+bcrypt │  │ Tenant scope │  │ AppException, 404, 403   ││
│  └────────────┘  └──────────────┘  └──────────────────────────┘│
└──────┬───────────────┬──────────────────┬───────────────────────┘
       │               │                  │
       ▼               ▼                  ▼
┌──────────────┐ ┌───────────────┐ ┌──────────────────┐
│ PostgreSQL   │ │ MongoDB Atlas │ │ Redis            │
│ (Supabase)   │ │               │ │ (Celery broker)  │
│ 44 tables    │ │ 12 collections│ │ + result backend │
└──────────────┘ └───────────────┘ └────────┬─────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Celery Workers   │
                                   │ 28+ scheduled    │
                                   │ tasks            │
                                   └────────┬─────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
           ┌──────────────┐      ┌──────────────────┐    ┌─────────────────┐
           │OpenPrescribing│      │ NHS ODS API      │    │ Google Gemini   │
           │ + Scrapfly    │      │ (Org hierarchy)  │    │ (AI/Clinical)   │
           └──────────────┘      └──────────────────┘    └─────────────────┘
```

### 2.2 Application Factory

**File:** `backend/app/main.py`

The app uses a factory pattern via `create_app()`:

1. **Startup events:** Connect to MongoDB, initialize Beanie ODM with 12 document models, set up OpenTelemetry (if configured)
2. **Shutdown events:** Disconnect MongoDB
3. **Middleware registration:** CORS, Request ID, Tenant Context, Org Scoping, Request Logging, Security Headers
4. **Router mounting:** 37 routers registered under `/api` prefix
5. **Exception handlers:** Custom `AppException`, generic catch-all

### 2.3 Dual-Database Design

| Database | Purpose | Technology | Key Data |
|----------|---------|-----------|----------|
| **PostgreSQL** | Relational data, RBAC, audit | SQLAlchemy 2.0 async + Alembic | Users, tenants, orgs, interventions, formulary, audit logs, notifications |
| **MongoDB** | Clinical document store | Motor + Beanie ODM | Patients, prescriptions, opportunities, medications, tariff prices, ICB reports |

**Why dual databases?**
- PostgreSQL handles strict relational integrity (users, RBAC, org hierarchy, financial audit trails)
- MongoDB handles high-volume clinical documents with flexible schemas (patient records, prescriptions, opportunities with nested spending data)

---

## 3. Multi-Tenancy & RBAC

### 3.1 Tenant Isolation

Tenant isolation is enforced at four layers:

1. **Middleware** (`backend/app/middleware.py`): Extracts `tenant_id` from `X-Tenant-ID` header, injects into `request.state.tenant_id`
2. **Dependencies** (`backend/app/dependencies.py`): `get_tenant_id()` resolves tenant from header → JWT claims → `user.tenant_id` → `user.icb_id`
3. **Session tagging**: `get_tenant_scoped_db()` tags the SQLAlchemy session with `info["tenant_id"]` for automatic query scoping
4. **Org scoping middleware**: Extracts `X-Org-Level` and `X-Org-ODS-Code` headers for per-request org context

### 3.2 Role Definitions

**File:** `backend/app/core/permissions.py`

| Role | Scope | Data Zones | Description |
|------|-------|-----------|-------------|
| `system_admin` | Global | 1, 2, 3 | Full system access |
| `admin` | Global | 1, 2, 3 | Admin alias |
| `icb_manager` | ICB tenant | 1, 2 | ICB management |
| `icb_leader` | ICB tenant | 1, 2 | ICB leadership/board |
| `icb_pharmacist` | ICB tenant | 1, 2, 3 | ICB clinical pharmacist |
| `sub_icb_lead` | Sub-ICB | 1, 2 | Sub-ICB leadership |
| `pcn_pharmacist` | PCN ODS codes | 1, 2, 3 | Scoped to assigned PCNs |
| `practice_pharmacist` | Practice ODS code | 1, 2, 3 | Scoped to single practice |
| `pharmacy_technician` | Practice ODS code | 1, 2 | Limited features |
| `pharmacist` | Legacy | 1, 2, 3 | Legacy alias |
| `technician` | Legacy | 1, 2 | Legacy alias |
| `gp` | Practice | 1, 2 | General practitioner |
| `practice_user` | Practice | 1 | Basic practice user |

### 3.3 Data Zones

| Zone | Access Level | Data Type | Example |
|------|-------------|-----------|---------|
| **Zone 1** | All roles | Aggregated ICB-level data | Dashboard summaries, workstream totals |
| **Zone 2** | Pharmacist+ | Practice-level data | Practice-specific opportunities, spending |
| **Zone 3** | Clinical staff only | Patient PII | NHS numbers, patient names, addresses |

### 3.4 Authentication Flow

**File:** `backend/app/core/security.py`

1. User submits `email` + `password` to `POST /api/auth/login`
2. Password verified with bcrypt (12 rounds)
3. Access token issued (JWT HS256, 30-minute expiry)
4. Refresh token issued (JWT HS256, 7-day expiry)
5. Frontend stores tokens, attaches `Authorization: Bearer <token>` header
6. `get_current_user` dependency decodes JWT, loads user from DB
7. `get_current_active_user` checks `is_active` flag
8. Role checkers validate permissions per endpoint

### 3.5 Email-Based Auto-Scoping

**File:** `backend/app/services/org_resolution_service.py`

When a user registers, the system automatically resolves their organization:
- Email domain (e.g., `@nhs.net`, `@syicb.nhs.uk`) → `OrgEmailDomain` table lookup
- Matched domain → auto-assign `tenant_id`, `icb_id`, `practice_ods_code` or `pcn_ods_codes`
- `OrgResolutionService` handles the full chain: email → domain → org → tenant → auto-create user with correct scope

---

## 4. Database Design

### 4.1 PostgreSQL Models (44 Tables)

**Connection:** `backend/app/database.py`
- Engine: `create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=300)`
- Session: `async_sessionmaker(AsyncSession, expire_on_commit=False)`

#### Core Organization Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `icbs` | id, name, ods_code, postcode, address, phone, last_ods_sync | Integrated Care Boards |
| `pcns` | id, name, ods_code, postcode, icb_id (FK), sub_icb_ods_code | Primary Care Networks |
| `practices` | id, name, ods_code, postcode, icb_id (FK), pcn_id (FK), sub_icb_ods_code | GP Practices |
| `ods_organisations` | id, tenant_id, ods_code, name, org_type, parent_ods_code, status, address, postcode, clinical_system | Full 4-level NHS ODS hierarchy (ICB/SUB_ICB/PCN/PRACTICE) |
| `tenants` | id, name, icb_ods_code, is_active, onboarded_at | Multi-tenant isolation |
| `org_email_domains` | id, domain, org_type, org_ods_code, tenant_id | Email domain → org mapping |

#### User & Auth Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `users` | id, email, hashed_password, first_name, last_name, role, is_active, tenant_id, icb_id, practice_ods_code, pcn_ods_codes, org_level | User accounts with RBAC |
| `audit_logs` | id, actor_id, actor_role, action, resource_type, resource_id, details, tenant_id, created_at | Immutable audit trail |

#### Clinical & Medication Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `patients` | id, nhs_number, first_name, last_name, date_of_birth, practice_id, is_deleted | Patient records (soft-deletable) |
| `medications` | id, name, bnf_code, generic_name, form, strength, unit_cost | Medication catalog |
| `switching_rules` | id, name, workstream, from_medication_id, to_medication_id, criteria_json, is_active | Switching logic rules |
| `switching_opportunities` | id, patient_id, switching_rule_id, status, estimated_savings, assigned_to | Identified switch opportunities |
| `prescribing_data` | id, practice_ods_code, bnf_code, period, items, quantity, actual_cost | Historical prescribing records |
| `formulary_entries` | id, tenant_id, bnf_code, drug_name, therapeutic_area, preferred, notes | ICB formulary drugs |
| `formulary_snapshots` | id, tenant_id, snapshot_date, data | Point-in-time formulary |

#### Intervention & Savings Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `action_sheets` | id, tenant_id, practice_ods_code, workstream, status, content, approved_by | Approved action sheets |
| `interventions` | id, tenant_id, name, workstream, status, forecast_savings, realized_savings, started_at, completed_at | Intervention lifecycle tracking |
| `realized_savings` | id, tenant_id, practice_ods_code, period, actual_savings, workstream | Cumulative realized savings |
| `realized_saving_monthly` | id, tenant_id, period, workstream, practice_ods_code, amount | Monthly realized savings breakdown |

#### AI & Rule Set Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `ai_rule_sets` | id, tenant_id, query_text, rule_set_json (JSONB), transpiled_query, target_system, version, parent_id, status (draft/approved/rejected), ai_confidence, safety_warnings, guardrail_safe, flagged_phrases | AI-generated clinical search rule sets |
| `ai_decision_audit` | id, tenant_id, action, input_summary, output_summary, guardrail_status, human_action, human_notes, created_at | Immutable AI decision audit trail |
| `weekly_recommendations` | id, tenant_id, practice_ods_code, pcn_ods_code, week_commencing, opportunity_id, opportunity_title, recommendation_type, rationale, estimated_savings, priority_score, actioned, deferred, rejected, email_sent | Weekly AI-generated recommendations |

#### Notification & Communication Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `notifications` | id, user_id, title, message, type, is_read, created_at | In-app notifications |
| `email_logs` | id, to_email, subject, status, provider, sent_at | Email delivery audit log |
| `patient_letters` | id, patient_id, intervention_id, content, language, format, sent_at | Patient communication letters |

#### Data Import & Monitoring Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `import_jobs` | id, source, status, file_path, records_processed, errors, started_at, completed_at | Data import job tracking |
| `data_freshness` | id, source, last_synced_at, record_count, status | Sync freshness monitoring |
| `patent_expiries` | id, drug_name, bnf_code, patent_holder, expiry_date, status, watch_list, source | Patent expiry monitoring |
| `price_snapshots` | id, bnf_code, drug_name, price_pence, source, snapshot_date | Price discovery snapshots |
| `pii_patient_records` | id, tenant_id, patient_id, encrypted_data, access_level | Zone 3 PII data |
| `pii_access_logs` | id, user_id, patient_id, action, accessed_at | PII access audit |
| `epact_records` | id, tenant_id, practice_ods_code, bnf_code, period, items, quantity, actual_cost | ePACT2 import records |
| `rebate_agreements` | id, tenant_id, drug_name, bnf_code, manufacturer, rebate_pct, start_date, end_date | Rebate agreements |
| `patient_worklist_items` | id, tenant_id, patient_id, intervention_id, status, assigned_to, due_date | Worklist management |

### 4.2 MongoDB Document Models (12 Collections)

**Connection:** `backend/app/mongodb.py`
- Client: `AsyncIOMotorClient(MONGODB_URI)`
- Database: `qipp_patients`
- ODM: Beanie (Pydantic-based document models)

#### PatientDocument (`patient_mongo.py`)

```python
class PatientDocument(Document):
    nhs_number: str                    # Unique NHS patient identifier
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    postcode: str | None
    practice_ods_code: str             # GP practice ODS code
    icb_id: str | None
    pcn_ods_code: str | None
    risk_level: RiskLevel              # low/medium/high/critical
    is_eligible: bool                  # Eligible for medication switch
    current_medications: list[dict]    # Embedded medication list
    allergies: list[dict]              # Embedded allergy list
    conditions: list[dict]             # ICD-coded conditions
    flags: list[str]                   # Clinical flags
    clinical_reviews: list[dict]       # Review history
    smoking_status: str | None
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "patients"
        indexes = [
            "nhs_number", "practice_ods_code", "icb_id",
            "risk_level", "is_eligible"
        ]
```

#### PrescriptionDocument (`patient_mongo.py`)

```python
class PrescriptionDocument(Document):
    patient_id: str                    # Reference to PatientDocument
    nhs_number: str
    bnf_code: str                      # 15-char BNF code
    drug_name: str
    quantity: float
    items: int
    actual_cost: float
    prescribed_date: datetime
    practice_ods_code: str
    prescriber: str | None
    switch_status: SwitchStatus        # not_applicable/eligible/switched/refused/switchback

    class Settings:
        name = "prescriptions"
```

#### OpportunityDocument (`opportunity_mongo.py`)

```python
class OpportunityDocument(Document):
    org_level: str                     # practice/pcn/sub_icb/icb
    practice_ods_code: str | None
    pcn_ods_code: str | None
    sub_icb_ods_code: str | None
    icb_id: str | None
    workstream: str                    # STATINS, DOACs, SGLT2, DPP4, PPI, etc.
    therapeutic_area: str | None       # Cardiovascular, Endocrine/Diabetes, etc.
    description: str
    estimated_annual_savings: float
    patients_affected: int
    effort_reward_score: float
    current_expensive_bnf: str         # Expensive drug BNF code/name
    target_cheap_bnf: str              # Target cheaper alternative
    status: str                        # IDENTIFIED/IN_PROGRESS/COMPLETED/REJECTED
    created_at: datetime
    updated_at: datetime
    spending_data_fetched: bool
    spending_items: list[SpendingLineItem]  # Embedded spending breakdown
    clinical_comments: list[dict]      # Embedded clinical comments

    class Settings:
        name = "opportunities"
        indexes = [
            "org_level", "practice_ods_code", "pcn_ods_code",
            "sub_icb_ods_code", "icb_id", "workstream", "status"
        ]
```

#### SpendingLineItem (Embedded in OpportunityDocument)

```python
class SpendingLineItem(BaseModel):
    bnf_code: str
    bnf_name: str
    items: int
    quantity: float
    actual_cost: float
    unit_cost: float | None
    date: str
```

#### MedicationDocument (`medication_mongo.py`)

```python
class MedicationDocument(Document):
    bnf_code: str                      # Full 15-char BNF presentation code
    bnf_name: str                      # Full BNF name
    bnf_chapter: str                   # BNF chapter code
    bnf_section: str                   # BNF section code
    generic_name: str | None
    is_generic: bool
    workstream: MedicationWorkstream | None  # Mapped QIPP workstream
    unit_cost: float | None
    pack_size: int | None
    form: str | None                   # tablet/capsule/injection/inhaler
    strength: str | None
    manufacturer: str | None
    alternatives: list[str]            # BNF codes of alternatives
    tags: list[str]                    # User-defined tags
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "medications"
        indexes = ["bnf_code", "workstream", "is_generic"]
```

#### TariffPriceDocument (`tariff_mongo.py`)

```python
class TariffPriceDocument(Document):
    vmpp_id: str                       # VMPP identifier
    vmpp: str                          # VMPP name
    product: str                       # Product name
    tariff_category: str               # Category A/C/M/E
    price_pence: int                   # Price in pence
    pack_size: float | None
    date: str                          # Tariff period (YYYY-MM)
    concession: bool                   # Price concession flag

    class Settings:
        name = "tariff_prices"
        indexes = ["vmpp_id", "product", "date", "concession"]
```

#### Other MongoDB Collections

| Collection | Document Model | Purpose |
|-----------|---------------|---------|
| `patient_analytics` | `PatientAnalyticsDocument` | Computed risk scores, eligibility, trends |
| `sync_logs` | `SyncLogDocument` | Data sync audit trail (source, status, records) |
| `practice_measures` | `PracticeMeasureDocument` | NHS QIPP measures cached per practice |
| `drug_classes` | `DrugClassDocument` | BNF chapter/section hierarchy |
| `medication_sync_logs` | `MedicationSyncLogDocument` | Medication catalog sync audit |
| `tariff_sync_logs` | `TariffSyncLogDocument` | Drug tariff sync audit |
| `icb_reports` | `ICBReportDocument` | Monthly ICB performance reports |

---

## 5. Pydantic Schemas

**Location:** `backend/app/schemas/`

### 5.1 Authentication Schemas (`auth.py`)

| Schema | Fields | Usage |
|--------|--------|-------|
| `LoginRequest` | email: str, password: str | POST /api/auth/login |
| `TokenResponse` | access_token: str, refresh_token: str, token_type: str | Login response |
| `RefreshRequest` | refresh_token: str | POST /api/auth/refresh |
| `AccessTokenResponse` | access_token: str, token_type: str | Refresh response |
| `UserProfile` | id, email, first_name, last_name, role, tenant_id, icb_id, practice_ods_code, pcn_ods_codes, org_level | GET /api/auth/me |

### 5.2 Common Enums (`common.py`)

| Enum | Values |
|------|--------|
| `UserRole` | system_admin, admin, icb_manager, icb_leader, icb_pharmacist, sub_icb_lead, pcn_pharmacist, practice_pharmacist, pharmacy_technician, pharmacist, technician, gp, practice_user |
| `RiskLevel` | low, medium, high, critical |
| `OpportunityStatus` | identified, in_progress, limit_reached, completed, rejected |
| `ActionSheetStatus` | draft, pending_approval, approved, rejected |
| `ImportJobStatus` | pending, processing, completed, failed |
| `ClinicalSystem` | emis_web, systmone, vision |

### 5.3 Patient Schemas (`patient_v2.py`)

| Schema | Key Fields | Usage |
|--------|-----------|-------|
| `PatientCreateV2` | nhs_number, first_name, last_name, date_of_birth, gender, practice_ods_code, medications[], allergies[], conditions[] | Create patient |
| `PatientUpdateV2` | All optional fields | Update patient |
| `PatientSummary` | id, nhs_number, name, practice_ods_code, risk_level, is_eligible | List item |
| `PatientDetailV2` | Full patient record + prescriptions, reviews, flags | Detail view |
| `PrescriptionCreate` | bnf_code, drug_name, quantity, items, actual_cost, prescribed_date | Add prescription |
| `EligibilityCheck` | patient_id, is_eligible, eligible_workstreams[], reasons[] | Eligibility result |
| `RiskScoreResponse` | patient_id, overall_risk, score_breakdown{}, risk_factors[] | Risk assessment |

### 5.4 Opportunity Schemas (`opportunity.py`)

| Schema | Key Fields | Usage |
|--------|-----------|-------|
| `OpportunityResponse` | id, workstream, description, estimated_annual_savings, patients_affected, status, practice_ods_code | Single opportunity |
| `OpportunityListResponse` | items[], total, page, per_page, total_pages | Paginated list |
| `OpportunityStatusUpdate` | status: OpportunityStatus, clinical_notes?: str | Status change |
| `OpportunityAssign` | assigned_to_user_id: UUID | Assignment |

### 5.5 Clinical Search Schemas (`clinical_search.py`)

| Schema | Key Fields | Usage |
|--------|-----------|-------|
| `ClinicalSearchRequest` | query: str, target_system: str (emis_web/systmone/csv), context?: dict | AI clinical search |
| `ClinicalSearchResponse` | rule_set: dict, transpiled_query: str, confidence: float, safety_warnings: list, guardrail_result: dict | Search result |
| `ExclusionSuggestionRequest` | from_drug: str, to_drug: str, workstream?: str | Exclusion suggestions |
| `ExclusionSuggestionResponse` | suggestions: list[{criterion, severity, rationale}] | Exclusion list |
| `ActionSheetGenerateRequest` | workstream: str, from_drug: str, to_drug: str, practice_name?: str | Action sheet generation |
| `PatientLetterGenerateRequest` | patient_name: str, from_drug: str, to_drug: str, reason: str, language?: str | Patient letter |
| `PatientLetterBatchRequest` | patient_ids: list[str], template_key: str | Batch letters |

### 5.6 Dashboard Schemas (`dashboard.py`)

| Schema | Key Fields |
|--------|-----------|
| `DashboardSummary` | total_savings_potential, realized_savings, active_opportunities, completed_switches, realization_rate |
| `WorkstreamSummary` | workstream, potential_savings, realized_savings, opportunity_count, completion_rate |
| `PracticeSummary` | practice_name, ods_code, potential_savings, realized_savings, active_opportunities |

### 5.7 Savings Schemas (`savings.py`)

| Schema | Key Fields |
|--------|-----------|
| `SavingsSummary` | total_potential, total_realized, realization_rate, switches_completed |
| `SavingsByWorkstream` | workstream, potential, realized, rate, switches |
| `MonthlySavingsPoint` | month, potential, realized, cumulative |
| `CompletedSwitch` | patient_id, from_drug, to_drug, savings, switch_date, practice |
| `SavingsByStatusBreakdown` | status, count, total_savings |

### 5.8 Other Key Schemas

| File | Key Schemas |
|------|-------------|
| `medication.py` | `MedicationCreate/Update/Response`, `SwitchingRuleCreate/Update/Response` |
| `medication_v2.py` | `DrugClassResponse`, `MedicationStatsResponse`, `MedSyncLogResponse` |
| `action_sheet.py` | `ActionSheetCreate/Response/ListResponse` |
| `formulary.py` | `FormularyEntryCreate/Update/Response`, `FormularyBulkImport` |
| `intervention.py` | `InterventionCreate/Update/Response`, `InterventionStatusChange` |
| `notification.py` | `NotificationResponse/ListResponse` |
| `report.py` | `SavingsReport`, `WorkloadReport`, `ImportStatusResponse` |
| `icb.py` | `ICBCreate/Update/Response`, `PCNCreate/Response`, `PracticeCreate/Update/Response` |
| `tenant.py` | `TenantCreate/Update/Response` |
| `rebate.py` | `RebateCreate/Update/Response`, `RecommendationResponse` |

---

## 6. External API Integrations

This is the most critical section — documenting every external API the system calls, the exact endpoints, parameters, response schemas, and how the system uses each.

---

### 6.1 OpenPrescribing API

**Service File:** `backend/app/services/openprescribing_service.py`
**Class:** `OpenPrescribingService`
**Base URL:** `https://openprescribing.net/api/1.0`
**Authentication:** None (publicly available NHS data)
**Cloudflare Bypass:** All requests routed through Scrapfly (see §6.4)
**Caching:** 24-hour file cache in `data/scrapfly_cache/` with stale-cache fallback

#### Why Scrapfly?

OpenPrescribing.net is protected by Cloudflare Turnstile, which blocks direct API calls. The system uses Scrapfly's Anti-Scraping Protection (`asp=True`) with UK proxy (`country="GB"`) to bypass Cloudflare and fetch the JSON/CSV data. Each Scrapfly call is cached locally for 24 hours to minimize API costs.

#### Cache Strategy

```
1. Check local file cache: data/scrapfly_cache/{endpoint_key}.json
2. If fresh (< 24h old) → return cached data
3. If stale or missing → Scrapfly fetch → save to file → return
4. On Scrapfly failure → fall back to stale cache if available
5. For tariff CSV → additional fallback to manual backend/tariff.csv
```

#### Endpoint 1: BNF Code Search

```
GET /api/1.0/bnf_code/?q={query}&format=json&exact={true|false}
```

**Purpose:** Search the BNF (British National Formulary) code hierarchy — chapters, sections, paragraphs, chemicals, products, presentations.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | BNF code prefix or search term (e.g., "0601022" for DPP4 inhibitors) |
| `format` | string | Yes | Always `json` |
| `exact` | boolean | No | `true` for exact match, `false` for prefix/fuzzy match |

**Response Schema:**
```json
[
  {
    "type": "chemical",          // chapter/section/paragraph/chemical/product/presentation
    "id": "0601022B0",           // BNF code
    "name": "Sitagliptin",      // Drug/section name
    "section": "0601022"         // Parent section code
  }
]
```

**System Usage:**
- `search_bnf_codes(query, exact)` — Core BNF code lookup
- `get_bnf_sections()` — Fetch top-level BNF chapter/section hierarchy (no `q` param)
- `search_bnf_presentations(query)` — Alias for `search_bnf_codes(query, exact=False)`
- Used by the opportunity discovery engine to identify chemical codes per workstream
- Used by the medication sync task to build the medication catalog

**Cache Key:** `bnf_code_q={query}_exact={true|false}`

#### Endpoint 2: Spending by Organisation

```
GET /api/1.0/spending_by_org/?code={bnf_code}&org_type={type}&org={ods_code}&format=json
```

**Purpose:** Get prescribing spending data at any NHS hierarchy level — how much each org spends on a specific BNF code.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | BNF section/paragraph prefix (e.g., "0601022" for DPP4) |
| `org_type` | string | Yes | `practice`, `pcn`, `sicbl` (Sub-ICB), or `icb` |
| `org` | string | No | Specific ODS code to filter to one org |
| `format` | string | Yes | Always `json` |

**Response Schema:**
```json
[
  {
    "row_id": "C84001",          // ODS code of the org
    "row_name": "Practice Name", // Org name
    "date": "2025-12-01",        // Prescribing period
    "actual_cost": 12345.67,     // Total cost in GBP
    "items": 456,                // Number of prescription items
    "quantity": 7890             // Total quantity dispensed
  }
]
```

**System Usage:**
- `get_spending_by_org(bnf_code, org_type, org_code)` — Multi-level spending lookup
- `get_spending_by_practice(bnf_code)` — Backwards-compatible alias (practice-level)
- `get_practice_prescribing(practice_ods, bnf_code)` — All prescribing for a specific GP practice
- Used by opportunity discovery to calculate estimated savings per practice
- Used by the tariff router for spending analysis endpoints
- Used by the predictive service for spending forecast regression

**Cache Key:** `spending_by_org_code={bnf_code}_org={org_type}_{ods_code}`

#### Endpoint 3: National Spending by Chemical

```
GET /api/1.0/spending/?code={chemical_code}&format=json
```

**Purpose:** Get national-level spending breakdown for a specific chemical substance over time.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | BNF chemical code (e.g., "0601022B0" for Sitagliptin) |
| `format` | string | Yes | Always `json` |

**Response Schema:**
```json
[
  {
    "date": "2025-12-01",
    "actual_cost": 2345678.90,   // National total cost
    "items": 123456,             // National total items
    "quantity": 789012           // National total quantity
  }
]
```

**System Usage:**
- `get_spending_by_chemical(chemical_code)` — National spending trends
- Used in tariff router `/spending/national` endpoint
- Used for national benchmarking and trend analysis

**Cache Key:** `spending_code={chemical_code}`

#### Endpoint 4: Measures by Organisation

```
GET /api/1.0/measure_by_{level}/?org={ods_code}&format=json
```

Where `{level}` is one of: `practice`, `pcn`, `sicbl`, `icb`

**Purpose:** Fetch NHS QIPP quality measures (prescribing indicators) for a specific organisation. These are pre-computed by OpenPrescribing and identify areas where prescribing deviates from best practice.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `org` | string | Yes | ODS code of the organisation |
| `format` | string | Yes | Always `json` |

**Level → Endpoint Mapping:**
```python
ORG_LEVEL_TO_MEASURE_ENDPOINT = {
    "practice": "/measure_by_practice/",
    "pcn":      "/measure_by_pcn/",
    "sub_icb":  "/measure_by_sicbl/",
    "icb":      "/measure_by_icb/",
}
```

**Response Schema:**
```json
{
  "measures": [
    {
      "measure": "statin_intensity",    // Measure ID
      "name": "Statin prescribing",     // Human-readable name
      "numerator": 234,                 // Numerator value
      "denominator": 1000,              // Denominator value
      "calc_value": 0.234,              // Ratio
      "percentile": 45,                 // National percentile ranking
      "actual_cost": 56789.12,          // Total cost for this measure
      "date": "2025-12-01"             // Period
    }
  ]
}
```

**System Usage:**
- `get_measures_for_org(org_id, org_level)` — Multi-level measure fetcher
- `get_measures_for_practice(org_id)` — Backwards-compatible alias
- **Critical for opportunity generation** — the `generate_opportunities_for_org()` method calls this to find workstreams where an org has expensive prescribing patterns
- Measures are mapped to QIPP workstreams via `WORKSTREAM_MAPPINGS`

**Cache Key:** `measures_{org_level}_{org_id}`

#### Endpoint 5: Organisation Code Search

```
GET /api/1.0/org_code/?q={query}&org_type=practice&format=json
```

**Purpose:** Search for NHS organisations by name or ODS code.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (name or ODS code, min 2 chars) |
| `org_type` | string | Yes | `practice` (only type currently used) |
| `format` | string | Yes | Always `json` |

**Response Schema:**
```json
[
  {
    "code": "C84001",
    "name": "THE VILLAGE SURGERY",
    "type": "practice",
    "postcode": "S1 1AA",
    "setting": 4
  }
]
```

**System Usage:**
- `search_practice(query)` — Practice autocomplete search
- Used by the tariff router `/practices/search` endpoint

**Cache Key:** `org_code_q={query}`

#### Endpoint 6: Drug Tariff (CSV)

```
GET /api/1.0/tariff/?format=csv
```

**Purpose:** Download the complete NHS Drug Tariff as CSV — contains every drug price (Category A/C/M/E), pack sizes, VMPP identifiers, and price concession flags.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | Yes | `csv` for bulk download |

**Response:** Raw CSV text with headers:
```
vmpp_id,vmpp,product,tariff_category,price_pence,pack_size,date,concession
```

**Parsed Record Schema:**
```python
{
    "vmpp_id": "1234567",               # VMPP identifier
    "vmpp": "Atorvastatin 20mg tabs",   # VMPP name
    "product": "Atorvastatin",          # Product name
    "tariff_category": "Category M",    # A/C/M/E
    "price_pence": 234,                 # Price in pence
    "pack_size": 28.0,                  # Pack size
    "date": "2025-12",                  # Tariff period
    "concession": false                 # Price concession flag
}
```

**System Usage:**
- `get_tariff_prices(force)` → fetches CSV, parses via `_parse_tariff_csv()`, returns list of dicts
- Stored to MongoDB `tariff_prices` collection via sync task
- Used for unit cost calculations, price comparison, Category M monitoring
- Used to enrich opportunities with `expensive_unit_cost` and `cheap_unit_cost`
- Falls back to `backend/tariff.csv` (manually downloaded) if Scrapfly fails

**Cache Key:** `tariff.csv` in `data/scrapfly_cache/`

#### QIPP Workstream → BNF Prefix Mapping

The system maps 10 QIPP workstreams to BNF section/paragraph codes:

```python
QIPP_WORKSTREAM_QUERIES = {
    "DPP4":          "0601022",   # Dipeptidylpeptidase-4 inhibitors
    "SGLT2":         "0601023",   # SGLT-2 inhibitors
    "STATINS":       "0212000",   # Lipid-regulating drugs
    "ACE":           "0205051",   # ACE inhibitors
    "BETA_BLOCKERS": "0204000",   # Beta-adrenoceptor blocking drugs
}

WORKSTREAM_MAPPINGS = [
    {"measure_id": "statin_intensity",  "workstream": "STATINS",          "target_drug": "Atorvastatin (Generic)"},
    {"measure_id": "doac",              "workstream": "DOACs",            "target_drug": "Edoxaban"},
    {"measure_id": "sglt2",             "workstream": "SGLT2",            "target_drug": "Dapagliflozin"},
    {"measure_id": "dpp4",              "workstream": "DPP4",             "target_drug": "Alogliptin"},
    {"measure_id": "ppi",               "workstream": "PPI",              "target_drug": "Lansoprazole"},
    {"measure_id": "asthma",            "workstream": "ASTHMA_INHALERS",  "target_drug": "Clenil Modulite"},
    {"measure_id": "copd",              "workstream": "COPD_INHALERS",    "target_drug": "Formulary Trimbow/Trelegy"},
    {"measure_id": "antidepressant",    "workstream": "ANTIDEPRESSANTS",  "target_drug": "Sertraline"},
    {"measure_id": "pregabalin",        "workstream": "GABAPENTINOIDS",   "target_drug": "Pregabalin (Generic)"},
    {"measure_id": "glp1",              "workstream": "GLP1",             "target_drug": "Semaglutide/Dulaglutide optimization"},
]

THERAPEUTIC_AREA_MAP = {
    "STATINS": "Cardiovascular",
    "DOACs": "Cardiovascular",
    "SGLT2": "Endocrine/Diabetes",
    "DPP4": "Endocrine/Diabetes",
    "GLP1": "Endocrine/Diabetes",
    "PPI": "Gastro-Intestinal",
    "ASTHMA_INHALERS": "Respiratory",
    "COPD_INHALERS": "Respiratory",
    "ANTIDEPRESSANTS": "CNS/Mental Health",
    "GABAPENTINOIDS": "CNS/Pain",
}
```

#### Opportunity Generation Algorithm

The `generate_opportunities_for_org()` method:

1. Clear existing IDENTIFIED opportunities for the org at the requested level
2. Fetch measures from OpenPrescribing at the correct org level
3. For each measure, match to a QIPP workstream via `WORKSTREAM_MAPPINGS`
4. If `denominator > 0` and `numerator > 0`, calculate:
   - `patients_affected = max(numerator / 12, 1)`
   - `savings = actual_cost * 0.25` (25% savings assumption)
5. Apply minimum savings threshold by org level:
   - Practice: £500
   - PCN: £2,000
   - Sub-ICB: £10,000
   - ICB: £25,000
6. Calculate `effort_reward_score = savings / patients_affected`
7. Create `OpportunityDocument` in MongoDB with all org identifiers
8. Batch insert all opportunities

#### Aggregate Helper

```python
async def get_qipp_prescribing_data(self) -> dict[str, dict]:
```

Fetches BNF data + practice-level spending for **every** QIPP workstream in one call. Returns:
```python
{
    "DPP4": {
        "chemicals": ["0601022B0", "0601022K0", ...],
        "medications": [...],
        "spending_data": [...]
    },
    "SGLT2": { ... },
    ...
}
```

---

### 6.2 NHS ODS API (Organisation Data Service)

**Service File:** `backend/app/services/ods_loader.py`
**Base URL:** `https://directory.spineservices.nhs.uk/ORD/2-0-0`
**Authentication:** None (public NHS directory)
**HTTP Client:** `httpx.AsyncClient` (async, with redirects)
**Timeout:** 20 seconds per request, 0.01–0.1s sleep between requests

#### NHS Organisation Hierarchy

```
ICB (RO318)
  └── Sub-ICB Location (RO98, formerly CCG)
        └── PCN (RO272)
              └── GP Practice (RO76)
```

#### Role Codes

| Code | Organisation Type | Count (approx.) |
|------|------------------|-----------------|
| `RO318` | Integrated Care Board (ICB) | ~42 |
| `RO98` | Sub-ICB Location (formerly CCG) | ~106 |
| `RO272` | Primary Care Network (PCN) | ~1,300 |
| `RO76` | GP Practice | ~6,500 |

#### Relationship Types (Child → Parent)

| Relationship | Direction | Description |
|-------------|-----------|-------------|
| `RE5` | Sub-ICB → ICB | Sub-ICB Location reports to ICB (target role RO261 or RO318) |
| `RE4` | PCN → Sub-ICB | PCN belongs to Sub-ICB Location (target role RO98) |
| `RE8` | Practice → PCN | Practice is member of PCN (target role RO272) |
| `RE4`/`RE6` | Practice → Sub-ICB | Practice belongs to Sub-ICB (target role RO98) |

**Important:** ODS relationships point **child → parent**, not parent → child. The system lists all orgs by role, fetches detail for each, and extracts the parent from the `Rels` section.

#### Endpoint 1: List Organisations by Role

```
GET /ORD/2-0-0/organisations?Roles={role}&Status=Active&Limit=1000&Offset={n}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `Roles` | string | Yes | Role code (RO318, RO98, RO272, RO76) |
| `Status` | string | Yes | Always `Active` |
| `Limit` | integer | Yes | Page size (max 1000) |
| `Offset` | integer | Yes | 1-based offset for pagination |

**Response Schema:**
```json
{
  "Organisations": [
    {
      "OrgId": "QF7",
      "Name": "NHS SOUTH YORKSHIRE INTEGRATED CARE BOARD",
      "PostCode": "S1 2GN",
      "Status": "Active",
      "OrgRecordClass": "RC1",
      "LastChangeDate": "2025-07-01"
    }
  ]
}
```

**Pagination:** The API is 1-based (`Offset=0` returns HTTP 406). Page through with `Offset += 1000` until `len(orgs) < PAGE_SIZE`.

#### Endpoint 2: Organisation Detail

```
GET /ORD/2-0-0/organisations/{ods_code}
```

**Response Schema (relevant sections):**
```json
{
  "Organisation": {
    "Name": "NHS SOUTH YORKSHIRE INTEGRATED CARE BOARD",
    "Status": "Active",
    "Roles": {
      "Role": [
        {"id": "RO318", "Status": "Active", "uniqueRoleId": 1234}
      ]
    },
    "Rels": {
      "Rel": [
        {
          "id": "RE5",
          "Status": "Active",
          "Target": {
            "OrgId": {"extension": "QF7"},
            "PrimaryRoleId": {"id": "RO318"}
          }
        }
      ]
    },
    "GeoLoc": {
      "Location": {
        "AddrLn1": "123 Main Street",
        "AddrLn2": "",
        "Town": "Sheffield",
        "County": "South Yorkshire",
        "PostCode": "S1 2GN"
      }
    },
    "Contacts": {
      "Contact": [
        {"type": "tel", "value": "0114 123 4567"}
      ]
    }
  }
}
```

#### Two-Phase Sync Algorithm

**File:** `backend/app/services/ods_loader.py` → `run_ods_sync()`

The system uses a two-phase approach to avoid DB statement timeouts:

**Phase 1: HTTP Collection (no DB connection)**
1. `collect_icbs(client)` — List all RO318 orgs, fetch detail for address/phone
2. `collect_sub_icbs(client, icb_codes)` — List all RO98 orgs, fetch detail, extract parent ICB via RE5 relationship. Skips orgs that also have RO318 role (ICBs with dual roles)
3. `collect_pcns_with_parents(client)` — List all RO272 orgs, fetch detail, extract parent Sub-ICB via RE4 (target RO98)
4. `collect_practices_with_parents(client)` — List all RO76 orgs, fetch detail, extract parent PCN via RE8 (target RO272)

**Phase 2: Batch DB Upsert (no API calls)**
1. `_db_upsert_icbs()` — Bulk upsert to `icbs` table using `psycopg2.extras.execute_values`
2. `_db_upsert_pcns()` — Bulk upsert to `pcns` table with correct `icb_id` and `sub_icb_ods_code`
3. `_db_upsert_practices()` — Bulk upsert to `practices` table with correct `icb_id`, `pcn_id`, `sub_icb_ods_code`
4. `_db_populate_ods_organisations()` — Populate full 4-level hierarchy in `ods_organisations` table

**Parent Extraction Logic:**
```python
def _extract_parent_from_rels(detail, rel_types, target_roles):
    """
    Extract parent ODS code from an org's Rels section.
    Looks for Active relationship matching rel_type AND target_role.
    """
    rels = detail.get("Rels", {}).get("Rel", [])
    for r in rels:
        if r["Status"] != "Active": continue
        if r["id"] not in rel_types: continue
        target = r["Target"]
        if target["PrimaryRoleId"]["id"] in target_roles:
            return target["OrgId"]["extension"]
    return None
```

#### Current Focus ICB

The system is currently configured for **South Yorkshire ICB (QF7)** with:
- 4 Sub-ICBs: 02P (Barnsley), 02X (Doncaster), 03L (Rotherham), 03N (Sheffield)
- 29 PCNs
- 171 GP Practices

---

### 6.3 Google Gemini AI API

**Service File:** `backend/app/ai/client.py`
**SDK:** `google-genai` Python SDK
**Model:** `gemini-2.0-flash`
**Temperature:** 0.2 (low creativity, high consistency)
**Max Tokens:** 8,192

#### Configuration

```python
GEMINI_API_KEY = settings.GEMINI_API_KEY      # API key from Google AI Studio
GEMINI_MODEL_NAME = "gemini-2.0-flash"        # Model ID
```

#### Client Architecture

The system uses a singleton Gemini client with two core functions:

```python
async def generate_text(prompt: str) -> str:
    """Generate text response. Strips markdown fences from output."""

async def generate_json(prompt: str) -> dict | list:
    """Generate JSON response. Strips markdown fences, parses JSON."""
```

Both functions:
1. Call Gemini with the prompt
2. Strip markdown code fences (` ```json ... ``` `) from the response
3. For `generate_json`, parse the cleaned text as JSON

#### AI Use Cases (7 Prompt Templates)

Each use case has a dedicated prompt builder in `backend/app/ai/prompts/`:

| Use Case | Prompt File | Input | Output |
|----------|------------|-------|--------|
| **Clinical Search Translation** | `clinical_search.py` | Plain English query + target system | Structured JSON rule set with inclusion/exclusion criteria, SNOMED/Read/BNF codes |
| **Exclusion Criteria Suggestions** | `exclusion_criteria.py` | Drug pair (from → to) | List of exclusions with severity (mandatory/recommended/optional) |
| **Action Sheet Generation** | `action_sheet.py` | Workstream, drug pair, practice | Intervention brief with step-by-step instructions, safety warnings |
| **Patient Letter Generation** | `patient_letter.py` | Patient name, drug pair, reason | Patient communication letter at reading age 12 |
| **Clinical Rationale** | `clinical_rationale.py` | Workstream, drug pair | Clinical + financial rationale summary |
| **Board Narrative** | `board_narrative.py` | ICB data, savings | Executive summary for ICB board pack |
| **Switchback Risk Prediction** | `switchback_risk.py` | Drug pair, historical data | Switchback risk assessment with probability |
| **Weekly Recommendations** | `weekly_recommendation.py` | Practice opportunities, capacity | Weekly practice opportunity selection |

#### AI Guardrails

**File:** `backend/app/ai/guardrails.py`

Every AI output passes through safety enforcement:

**15 Blocked Phrases:**
```python
BLOCKED_PHRASES = [
    "increase dose", "double dose", "triple dose",
    "stop taking", "discontinue immediately", "cease medication",
    "override clinical", "bypass safety", "ignore warning",
    "prescribe directly", "autonomous prescribing", "auto-prescribe",
    "without consultation", "no pharmacist review", "skip approval"
]
```

**Guardrail Pipeline:**
1. `validate_ai_output(text)` → scans for blocked phrases using regex
2. Returns `GuardrailResult(safe: bool, flagged_phrases: list, sanitised_output: str)`
3. If unsafe, flagged phrases are logged and the output is blocked
4. `stamp_disclaimer(text)` → appends: *"AI-generated content. Must be reviewed and approved by a qualified pharmacist before clinical use."*

#### AI Decision Audit Trail

Every AI interaction is logged immutably:

```python
AiDecisionAudit(
    action="translate|approve|reject|generate_action_sheet|generate_letter",
    input_summary=truncated_input[:2000],
    output_summary=truncated_output[:2000],
    guardrail_status="safe|unsafe|flagged",
    human_action="approved|rejected|pending",
    human_notes="Pharmacist review notes",
)
```

#### Rule Set Approval Workflow

```
Plain English Query
    → Gemini AI Translation
    → Guardrail Validation
    → Rule Set Parser (JSON → ClinicalRuleSet dataclass)
    → Code Mapper (validate SNOMED/BNF codes)
    → Transpiler (EMIS XML / SystmOne text / CSV)
    → Save as DRAFT
    → Pharmacist Review
    → APPROVED or REJECTED
```

#### Parsers and Transpilers

**Rule Set Parser** (`backend/app/ai/parsers/rule_set_parser.py`):
- Parses Gemini JSON → `ClinicalRuleSet` dataclass
- Sub-dataclasses: `CriterionRule`, `MedicationHistoryCheck`, `SwitchbackCheck`

**Code Mapper** (`backend/app/ai/parsers/code_mapper.py`):
- Validates SNOMED/BNF codes against local seed cache
- Flags unverified codes for manual pharmacist review

**Transpilers:**
| Transpiler | File | Output Format |
|-----------|------|---------------|
| EMIS Web | `emis_transpiler.py` | XML for Population Reporting |
| SystmOne | `systmone_transpiler.py` | Structured text report format |
| CSV Worklist | `csv_transpiler.py` | CSV template with 20 blank patient rows |

---

### 6.4 Scrapfly API

**Service File:** `backend/app/services/openprescribing_service.py` (embedded in `_scrapfly_fetch()`)
**SDK:** `scrapfly-sdk` Python package
**Purpose:** Cloudflare Turnstile bypass for OpenPrescribing.net

#### Configuration

```python
SCRAPFLY_API_KEY = settings.SCRAPFLY_API_KEY  # From .env
SCRAPFLY_DATA_DIR = "./data/scrapfly_cache"   # Local file cache directory
```

#### How It Works

```python
from scrapfly import ScrapeConfig, ScrapflyClient

client = ScrapflyClient(key=api_key)
response = client.scrape(ScrapeConfig(
    url="https://openprescribing.net/api/1.0/spending_by_org/?...",
    asp=True,       # Anti-Scraping Protection — Cloudflare bypass
    country="GB",   # UK proxy for NHS site
))
content = response.scrape_result["content"]  # Raw page content (JSON/CSV text)
```

**Key Parameters:**
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `asp` | `True` | Enable Anti-Scraping Protection (Cloudflare bypass) |
| `country` | `"GB"` | Use UK proxy (required for NHS sites) |
| `url` | Full OpenPrescribing URL | Target URL to fetch |

**Response:** `scrape_result["content"]` contains the raw page content. For JSON API endpoints, this is usually raw JSON but sometimes wrapped in HTML. The system extracts JSON using regex fallback:

```python
if not (json_text.startswith("[") or json_text.startswith("{")):
    match = re.search(r"(\[.*\]|\{.*\})", json_text, re.DOTALL)
    if match:
        json_text = match.group(1)
```

#### Cost Optimization

Each Scrapfly API call costs credits. The system minimizes costs by:
1. Caching every response to local files (24h freshness)
2. Checking cache before making any Scrapfly call
3. Falling back to stale cache on Scrapfly failure
4. Manual tariff.csv fallback for Drug Tariff data

---

### 6.5 NHS Drug Tariff (NHSBSA)

The Drug Tariff is accessed **through OpenPrescribing's `/tariff/` endpoint** (see §6.1, Endpoint 6), not directly from NHSBSA. The flow:

```
OpenPrescribing /api/1.0/tariff/?format=csv
    → Scrapfly (Cloudflare bypass)
    → Local CSV cache (data/scrapfly_cache/tariff.csv)
    → _parse_tariff_csv() → list of dicts
    → Stored to MongoDB tariff_prices collection
```

**Tariff Categories:**
| Category | Description |
|----------|------------|
| Category A | Readily available generics — based on weighted average of manufacturer prices |
| Category C | Products with only one supplier (branded) |
| Category M | Most commonly prescribed generics — price set by DHSC quarterly |
| Category E | Extemporaneously prepared items |

**Price Concessions:** When a generic drug experiences supply issues, NHSBSA grants temporary price concessions (higher reimbursement). The `concession` field flags these.

---

### 6.6 GOV.UK Notify API

**Service File:** `backend/app/services/notification_service.py` (GovUKNotifyChannel)
**Purpose:** NHS-approved notification service for sending emails and SMS to NHS staff
**SDK:** `notifications-python-client`

#### Configuration

```python
GOVUK_NOTIFY_API_KEY = settings.GOVUK_NOTIFY_API_KEY
GOVUK_NOTIFY_TEMPLATE_ACTION_SHEET = settings.GOVUK_NOTIFY_TEMPLATE_ACTION_SHEET
GOVUK_NOTIFY_TEMPLATE_RECOMMENDATION = settings.GOVUK_NOTIFY_TEMPLATE_RECOMMENDATION
GOVUK_NOTIFY_TEMPLATE_ALERT = settings.GOVUK_NOTIFY_TEMPLATE_ALERT
```

#### Usage

GOV.UK Notify uses pre-approved **template IDs** (created in the GOV.UK Notify dashboard). The system sends:

1. **Action Sheet Notifications** — when a new action sheet is generated for a practice
2. **Weekly Recommendation Emails** — Monday morning digest of recommended opportunities
3. **Alert Notifications** — price concession alerts, supply risk warnings

**API Call Pattern:**
```python
from notifications_python_client import NotificationsAPIClient

client = NotificationsAPIClient(api_key)
client.send_email_notification(
    email_address="pharmacist@nhs.net",
    template_id="template-uuid-here",
    personalisation={
        "practice_name": "The Village Surgery",
        "workstream": "STATINS",
        "savings_amount": "£12,345",
    }
)
```

**Why GOV.UK Notify?** It's the UK Government's official notification platform, pre-approved for NHS use. Messages pass through GDS (Government Digital Service) infrastructure, ensuring compliance with NHS data handling requirements.

---

### 6.7 Resend Email API

**Service File:** `backend/app/services/notification_service.py` (EmailChannel)
**Purpose:** Primary email delivery for non-NHS-specific communications
**SDK:** `resend` Python package

#### Configuration

```python
RESEND_API_KEY = settings.RESEND_API_KEY
EMAIL_FROM_ADDRESS = settings.EMAIL_FROM_ADDRESS    # e.g., "noreply@qipp.health"
EMAIL_FROM_NAME = settings.EMAIL_FROM_NAME          # e.g., "QIPP Medicines Optimization"
```

#### Usage

```python
import resend

resend.api_key = api_key
resend.Emails.send({
    "from": f"{from_name} <{from_address}>",
    "to": ["user@example.com"],
    "subject": "Your Weekly QIPP Report",
    "html": "<h1>Weekly Report</h1>...",
})
```

**Used for:**
- User invitation emails
- Password reset emails
- Weekly digest emails
- Patient letter batch emails
- Report delivery

---

### 6.8 Twilio SMS API

**Service File:** `backend/app/services/notification_service.py` (SmsChannel)
**Purpose:** SMS notifications for urgent alerts
**SDK:** `twilio` Python package

#### Configuration

```python
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_FROM_NUMBER = settings.TWILIO_FROM_NUMBER    # e.g., "+447911123456"
NOTIFICATIONS_SMS_ENABLED = settings.NOTIFICATIONS_SMS_ENABLED  # Feature flag
```

#### Usage

```python
from twilio.rest import Client

client = Client(account_sid, auth_token)
message = client.messages.create(
    body="ALERT: Price concession granted for Atorvastatin 20mg. Review impact on STATINS workstream.",
    from_=from_number,
    to="+447911999999",
)
```

**Used for:**
- Urgent price concession alerts
- Supply risk notifications
- Critical system alerts

---

### 6.9 SMTP Email (Fallback)

**Purpose:** Fallback email delivery when Resend is unavailable
**Library:** Python `smtplib` (stdlib)

#### Configuration

```python
SMTP_HOST = settings.SMTP_HOST          # e.g., "smtp.gmail.com"
SMTP_PORT = settings.SMTP_PORT          # e.g., 587
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD
SMTP_USE_TLS = settings.SMTP_USE_TLS   # True
```

The notification service tries Resend first, falls back to SMTP on failure.

---

### 6.10 ePACT2 (NHS BSA)

**Service File:** `backend/app/services/epact_service.py`
**Purpose:** Import detailed prescribing data from NHS Business Services Authority
**Integration Type:** CSV file upload (not direct API — data exported from ePACT2 portal)

#### Configuration

```python
EPACT2_BASE_URL = settings.EPACT2_BASE_URL
EPACT2_API_KEY = settings.EPACT2_API_KEY
EPACT2_USERNAME = settings.EPACT2_USERNAME
EPACT2_PASSWORD = settings.EPACT2_PASSWORD
```

#### Data Flow

```
ePACT2 Portal (manual CSV export)
    → Upload via POST /api/data-import/epact2
    → Background Celery task processes CSV
    → Records stored in epact_records table
    → Used for realized savings calculation
```

**CSV Format:** Practice-level prescribing data with columns:
- `practice_ods_code`, `bnf_code`, `bnf_name`, `period`, `items`, `quantity`, `actual_cost`

**Note:** ePACT2 is moving toward API access, but current integration is CSV-based. The system is pre-configured with API credentials for future direct integration.

---

### 6.11 NHS Digital dm+d (Dictionary of Medicines and Devices)

**Service File:** `backend/app/services/dmd_sync_service.py`
**Purpose:** Authoritative NHS product reference data — maps BNF codes to VMPs, VMPPs, AMPs
**Integration Type:** Periodic data sync

#### Data Hierarchy

```
VTM (Virtual Therapeutic Moiety)     — e.g., "Atorvastatin"
  └── VMP (Virtual Medicinal Product)  — e.g., "Atorvastatin 20mg tablets"
        └── VMPP (Virtual Medicinal Product Pack) — e.g., "Atorvastatin 20mg tablets x28"
              └── AMP (Actual Medicinal Product)   — e.g., "Lipitor 20mg tablets"
                    └── AMPP (Actual Medicinal Product Pack) — e.g., "Lipitor 20mg tablets x28"
```

**Used for:**
- Mapping between BNF codes and dm+d identifiers
- Resolving VMPP IDs for Drug Tariff price lookups
- Product name standardization

**Storage:** `dmd_products` table in PostgreSQL (via `DMDProduct` model)

---

### 6.12 GP Connect (FHIR R4)

**Service File:** `backend/app/services/gp_connect_service.py`
**Purpose:** Real-time access to GP clinical systems (EMIS Web, SystmOne) via NHS Spine
**Protocol:** HL7 FHIR R4
**Authentication:** JWT + mutual TLS (mTLS)

#### Architecture

```
QIPP System
    → JWT Token (signed with system cert)
    → NHS Spine Secure Proxy (SSP)
    → GP System (EMIS/SystmOne)
    → FHIR R4 Response
```

#### FHIR Resources Used

| Resource | Purpose | Example |
|----------|---------|---------|
| `Patient` | Demographics, NHS number | `GET /Patient/{nhs_number}` |
| `MedicationRequest` | Current prescriptions | `GET /MedicationRequest?patient={id}` |
| `MedicationStatement` | Medication history | `GET /MedicationStatement?patient={id}` |
| `AllergyIntolerance` | Allergy records | `GET /AllergyIntolerance?patient={id}` |
| `Condition` | Clinical conditions (ICD/SNOMED) | `GET /Condition?patient={id}` |

#### Authentication Flow

1. System generates JWT signed with registered certificate
2. JWT includes: `iss` (system ID), `sub` (practitioner ID), `aud` (target system URL), `exp`, `iat`
3. Request sent via NHS Spine Secure Proxy with mTLS
4. SSP validates JWT and forwards to target GP system
5. GP system returns FHIR R4 JSON response

**Note:** GP Connect integration requires NHS registration and certificate provisioning. The system is architecturally ready but requires per-ICB onboarding with NHS Digital.

---

## 7. Background Tasks (Celery)

**Broker:** Redis (`CELERY_BROKER_URL`)
**Result Backend:** Redis (`CELERY_RESULT_BACKEND`)
**Task Files:** `backend/app/tasks/`

### 7.1 Celery Beat Schedule

| Schedule | Task | Description |
|----------|------|-------------|
| Every 30 min | `sync_patient_data_task` | Sync patient records from clinical systems |
| Every 30 min | `sync_medications_data_task` | Sync medication catalog from OpenPrescribing BNF codes |
| Every 35 min | `compute_patient_analytics_task` | Recompute risk scores, eligibility, trends |
| Daily 02:00 | `sync_ods_data` | Refresh NHS ODS organisation hierarchy |
| Daily 02:00 | `discover_opportunities` | Run opportunity discovery across all workstreams |
| Daily 03:00 | `scan_for_switchbacks` | Detect patients who reverted to expensive drug |
| Daily 04:00 | `refresh_supply_risk_data` | Update supply risk flags from Drug Tariff |
| Weekly Mon 06:00 | `generate_weekly_recommendations` | AI-powered weekly practice recommendations |
| Weekly Mon 07:00 | `send_weekly_email_digests` | Send recommendation digests to pharmacists |
| Monthly 1st | `generate_monthly_reports_task` | Generate ICB monthly performance reports |
| Monthly 1st | `refresh_drug_tariff_prices` | Full Drug Tariff CSV refresh |
| Monthly 1st | `scan_for_patent_expiries` | Check for upcoming patent expiries |
| Monthly 15th | `check_price_concessions` | Check for new NHSBSA price concessions |

### 7.2 Task Queues

| Queue | Tasks |
|-------|-------|
| `patient_sync` | Patient data sync, analytics computation |
| `medication_sync` | Medication catalog sync, BNF data |
| `notifications` | Email digests, notification delivery |
| `reports` | Monthly report generation |
| `ai` | Weekly recommendations, clinical search |
| `pricing` | Tariff refresh, price concessions, supply risk |

### 7.3 Weekly Recommendation Engine

**File:** `backend/app/tasks/recommendation_tasks.py`

**Algorithm:**
1. Query MongoDB for all IDENTIFIED opportunities
2. Group by `practice_ods_code`
3. For each practice, check capacity (max 3 active recommendations)
4. Score opportunities using `ScoringEngine`:
   - Cash value (40%)
   - Certainty (20%)
   - Cohort size (15%)
   - Clinical suitability (15%)
   - Supply risk penalty (-10%)
5. Pick top `high_value` opportunity + top `quick_win` opportunity
6. Store as `WeeklyRecommendation` records
7. Mark `email_sent` and `notification_sent` after delivery

---

## 8. Middleware Stack

**File:** `backend/app/middleware.py`

Middleware executes in order for every request:

### 8.1 CORS Middleware

```python
CORSMiddleware(
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.2 Request ID Middleware

Attaches `UUID4` to `request.state.request_id`, returns as `X-Request-ID` response header.

### 8.3 Tenant Context Middleware

Extracts `X-Tenant-ID` header, stores in `request.state.tenant_id`. Exempts public paths: `/health`, `/docs`, `/redoc`, `/api/auth/login`, `/api/auth/refresh`.

### 8.4 Org Scoping Middleware

Extracts `X-Org-Level` (ICB/Sub-ICB/PCN/Practice) and `X-Org-ODS-Code` headers, stores in `request.state`.

### 8.5 Request Logging Middleware

Structured logging via `structlog`:
```json
{
  "event": "http_request",
  "method": "GET",
  "path": "/api/opportunities/summary",
  "status_code": 200,
  "duration_ms": 45,
  "request_id": "uuid",
  "tenant_id": "uuid"
}
```

### 8.6 Security Headers Middleware

Adds to all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000` (production only)

---

## 9. Frontend Architecture

**Location:** `health-guard-pro/`
**Framework:** React 18 + TypeScript + Vite
**UI Library:** Shadcn UI (Radix primitives) + TailwindCSS
**State Management:** TanStack Query (React Query v5)
**Routing:** react-router-dom
**Charts:** Recharts

### 9.1 API Client Layer (31 modules)

**Location:** `health-guard-pro/src/api/`

The frontend uses Axios with interceptors for:
- JWT token injection (`Authorization: Bearer <token>`)
- Tenant header injection (`X-Tenant-ID`)
- Automatic token refresh on 401 responses
- Request/response logging in development

Key API client files:
| File | Coverage |
|------|----------|
| `axios.ts` | Axios instance config, interceptors, token refresh |
| `auth.ts` | Login, logout, refresh, profile |
| `opportunities.ts` | Full opportunity lifecycle + workspace + register |
| `dashboardAnalytics.ts` | Role-based dashboard data |
| `clinicalSearch.ts` | AI clinical search, rule sets, action sheets |
| `tariff.ts` | Drug tariff prices, spending analysis |
| `odsHierarchy.ts` | ODS hierarchy sync and navigation |
| `patients.ts` | Patient CRUD, search, analytics |
| `medications.ts` | Medication catalog, search, sync |

### 9.2 Pages (44 components)

**Location:** `health-guard-pro/src/pages/`

Key pages by role:
| Role | Dashboard Page | Key Features |
|------|---------------|-------------|
| ICB Leader | `ICBLeadershipDashboard.tsx` | Savings by workstream, forecast variance, intervention status |
| ICB Pharmacist | `ICBPharmacistDashboard.tsx` | Opportunity pipeline, spend outliers, savings trajectory |
| PCN Pharmacist | `PCNPharmacistDashboard.tsx` | PCN-scoped workstreams, switch progress |
| Practice Staff | `PracticeStaffDashboard.tsx` | Action sheets, worklist, completion tracking |

---

## 10. Configuration Reference

**File:** `backend/app/config.py`

All settings loaded via pydantic-settings from `backend/.env`:

### Core Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | "QIPP Medicines Optimization" | Application name |
| `APP_ENV` | "development" | Environment (development/production) |
| `DEBUG` | `true` | Debug mode |
| `API_PREFIX` | "/api" | API route prefix |
| `CORS_ORIGINS` | localhost:3000,5173 | Allowed CORS origins |

### Databases

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL async connection string (`postgresql+asyncpg://...`) |
| `MONGODB_URI` | — | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | "qipp_patients" | MongoDB database name |
| `REDIS_URL` | — | Redis connection string |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | — | HS256 signing secret (min 32 chars) |
| `JWT_ALGORITHM` | "HS256" | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |

### External APIs

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENPRESCRIBING_BASE_URL` | `https://openprescribing.net/api/1.0` | OpenPrescribing API base |
| `SCRAPFLY_API_KEY` | — | Scrapfly Cloudflare bypass |
| `SCRAPFLY_DATA_DIR` | `./data/scrapfly_cache` | Local cache directory |
| `GEMINI_API_KEY` | — | Google Gemini AI |
| `GEMINI_MODEL_NAME` | "gemini-2.0-flash" | Gemini model |
| `RESEND_API_KEY` | — | Resend email service |
| `EMAIL_FROM_ADDRESS` | — | From email address |
| `EMAIL_FROM_NAME` | — | From display name |
| `TWILIO_ACCOUNT_SID` | — | Twilio SMS |
| `TWILIO_AUTH_TOKEN` | — | Twilio auth |
| `TWILIO_FROM_NUMBER` | — | Twilio phone number |
| `GOVUK_NOTIFY_API_KEY` | — | GOV.UK Notify |
| `GOVUK_NOTIFY_TEMPLATE_*` | — | Notify template IDs |
| `EPACT2_BASE_URL` | — | ePACT2 NHS BSA |
| `EPACT2_API_KEY` | — | ePACT2 auth |

### Celery

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | — | Redis broker |
| `CELERY_RESULT_BACKEND` | — | Redis result backend |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTIFICATIONS_EMAIL_ENABLED` | `false` | Enable email notifications |
| `NOTIFICATIONS_SMS_ENABLED` | `false` | Enable SMS notifications |

### Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_DSN` | — | Sentry error tracking |
| `OTLP_ENDPOINT` | — | OpenTelemetry endpoint |
| `LOG_LEVEL` | "INFO" | Logging level |
| `LOG_JSON` | `false` | JSON logging (production) |

### Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | 100 | General rate limit |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | 5 | Login rate limit |
| `MAX_UPLOAD_SIZE_MB` | 50 | File upload limit |

---

## 11. Key Services

**Location:** `backend/app/services/`

| Service | File | Purpose |
|---------|------|---------|
| `OpenPrescribingService` | `openprescribing_service.py` | OpenPrescribing API client with Scrapfly bypass, caching, opportunity generation |
| `ODS Loader` | `ods_loader.py` | NHS ODS hierarchy sync (two-phase: HTTP → DB) |
| `ODSService` | `ods_service.py` | ODS query methods (ancestry, descendants, sync) |
| `OrgResolutionService` | `org_resolution_service.py` | Email domain → org auto-scoping |
| `DashboardService` | `dashboard_service.py` | Dashboard data aggregation, org-scoped queries |
| `OpportunityDiscoveryEngine` | `opportunity_discovery.py` | Multi-level opportunity detection algorithm |
| `ScoringEngine` | (embedded) | Composite scoring: cash, certainty, cohort, clinical, supply, switch |
| `PredictiveService` | `predictive_service.py` | NumPy linear regression for 12-month spending forecasts |
| `ClinicalIntegrationService` | `clinical_integration_service.py` | EMIS/SystmOne/CSV worklist integration |
| `GPConnectService` | `gp_connect_service.py` | FHIR R4 clinical systems access |
| `NotificationManager` | `notification_service.py` | Multi-channel notification orchestration |
| `PricingEngine` | `pricing_engine.py` | Drug pricing calculations and scenarios |
| `FormularyService` | `formulary_service.py` | ICB formulary management |
| `PatentExpiryService` | `patent_expiry_service.py` | Patent monitoring and alerts |
| `PIIService` | `pii_service.py` | Zone 3 PII encryption and access control |

---

## 12. Deployment & Operations

### 12.1 Common Commands

```bash
make dev              # Backend dev server (port 8000)
make dev-frontend     # Frontend dev server (port 5173)
make dev-all          # Both simultaneously
make test             # Run all tests with coverage
make test-fast        # Stop on first failure
make lint             # Ruff check + format check
make format           # Auto-fix lint + format
make migrate          # Apply Alembic migrations
make migration msg="description"  # Create new migration
make seed             # Seed demo data
make celery           # Start Celery worker
make setup            # Full setup (install + migrate + seed)
```

### 12.2 Environment Setup

1. PostgreSQL (Supabase or local): Create database, set `DATABASE_URL`
2. MongoDB Atlas: Create cluster, set `MONGODB_URI`
3. Redis: Local or cloud instance for Celery
4. Python 3.11+ virtualenv: `backend/quid_venv/`
5. Node 18+: For frontend build
6. API Keys: Scrapfly, Gemini, Resend, Twilio, GOV.UK Notify (all optional — system degrades gracefully)

### 12.3 Data Initialization Flow

```
1. make migrate            → Create all PostgreSQL tables
2. make seed               → Seed admin user, demo tenant, South Yorkshire ICB
3. POST /api/admin/sync-ods/direct?target_icb_ods=QF7
                           → Fetch full NHS ODS hierarchy for South Yorkshire
4. POST /api/tariff/prices/sync
                           → Fetch Drug Tariff from OpenPrescribing
5. POST /api/opportunities/trigger-sync?ods_code=C84001&org_level=practice
                           → Generate opportunities for a practice
```

---

---

## 13. BNF Code System — Complete Reference

The British National Formulary (BNF) code system is the **backbone** of the QIPP platform. Every opportunity, every spending lookup, every drug switch, and every tariff price is identified and matched using BNF codes. This section is the definitive reference for how BNF codes work and how the system uses them.

---

### 13.1 BNF Code Structure & Hierarchy

BNF codes follow a **hierarchical structure** with increasing specificity from left to right. The NHS uses a 15-character alphanumeric code that encodes the entire drug classification:

```
Position:  01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
           ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
           │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
           │  │  │  │  │  │  │  │  │  └──┴──┴──┴──┴──┘  Presentation (pack/form)
           │  │  │  │  │  │  │  └──┘  Product code
           │  │  │  │  │  └──┴──┘     Chemical substance
           │  │  │  └──┘              Sub-paragraph
           │  │  └──┘                 Paragraph
           │  └──┘                    Section
           └──┘                       Chapter
```

#### Hierarchy Levels

| Level | Digits | Example | Meaning |
|-------|--------|---------|---------|
| **Chapter** | 2 | `02` | Cardiovascular System |
| **Section** | 4 | `0212` | Lipid-Regulating Drugs |
| **Paragraph** | 6 | `021200` | (Sub-classification within section) |
| **Sub-paragraph** | 7 | `0212000` | Lipid-regulating drugs (main group) |
| **Chemical** | 9 | `0212000B0` | Atorvastatin (chemical substance) |
| **Product** | 11 | `0212000B0AA` | Atorvastatin (branded product) |
| **Presentation** | 15 | `0212000B0AAABAB` | Atorvastatin 20mg tablets x28 |

#### Real-World Examples

```
Full BNF Code:   0 2 1 2 0 0 0 B 0 A A A B A B
                 │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
                 │ │ │ │ │ │ │ │ │ │ │ └─┴─┴─┘ Pack/form identifier
                 │ │ │ │ │ │ │ │ │ └─┘         Product (AA = generic)
                 │ │ │ │ │ │ │ └─┘             Chemical (B0 = Atorvastatin)
                 │ │ │ │ │ └─┘                 Sub-paragraph
                 │ │ │ │ └─┘                   Paragraph
                 │ │ └─┘                       Section (12 = Lipid-regulating)
                 └─┘                           Chapter (02 = Cardiovascular)
```

#### Key: Branded vs Generic Products

In the BNF code, positions 10-11 distinguish branded from generic:
- **`AA`** = Generic (non-proprietary) — e.g., `0212000B0AA` = Generic Atorvastatin
- **Other** = Branded product — e.g., `0212000B0BB` = Lipitor (branded Atorvastatin)

This is critical for QIPP — the system identifies opportunities where branded products (`B0AA`, `B0BB`) can be switched to cheaper generic equivalents.

#### BNF Chapters Relevant to QIPP

| Chapter | Name | QIPP Workstreams |
|---------|------|-----------------|
| **01** | Gastro-Intestinal System | PPI |
| **02** | Cardiovascular System | STATINS, DOACs, ACE, BETA_BLOCKERS |
| **03** | Respiratory System | ASTHMA_INHALERS, COPD_INHALERS |
| **04** | Central Nervous System | ANTIDEPRESSANTS, GABAPENTINOIDS |
| **06** | Endocrine System | DPP4, SGLT2, GLP1 |
| **07** | Obstetrics & Gynaecology | DESOGESTREL |

---

### 13.2 How the System Decomposes BNF Codes

**File:** `backend/app/services/medication_sync_service.py`

When medications are synced from OpenPrescribing, BNF codes are decomposed into hierarchy fields:

```python
bnf_code = "0212000B0AAABAB"

bnf_chapter   = bnf_code[:2]   # "02"         → Cardiovascular
bnf_section   = bnf_code[:4]   # "0212"       → Lipid-regulating drugs
bnf_paragraph = bnf_code[:6]   # "021200"     → Sub-classification
chemical      = bnf_code[:9]   # "0212000B0"  → Atorvastatin
```

These decomposed fields are stored on `MedicationDocument` in MongoDB, enabling hierarchical navigation (chapters → sections → paragraphs → drugs).

---

### 13.3 BNF Prefix Matching — The Core Pattern

The most fundamental pattern in the entire system is **BNF prefix matching** using `startswith()`. Instead of exact code matches, the system matches on prefixes to capture all products/presentations within a drug class:

```python
# Match ALL Atorvastatin products (branded + generic, all forms/packs):
PrescribingRecord.bnf_code.startswith("0212000B0")

# Match only BRANDED Atorvastatin:
PrescribingRecord.bnf_code.startswith("0212000B0AA")

# Match the entire Lipid-Regulating section:
PrescribingRecord.bnf_code.startswith("0212000")

# Match all Cardiovascular drugs:
PrescribingRecord.bnf_code.startswith("02")
```

This hierarchical prefix design means:
- A 2-digit prefix matches an entire **chapter** (thousands of drugs)
- A 7-digit prefix matches a **sub-paragraph** (dozens of drugs)
- A 9-digit prefix matches a specific **chemical** (all forms/packs of one drug)
- A 15-digit prefix matches a single **presentation** (one specific product)

---

### 13.4 QIPP Workstream → BNF Code Mappings

The system defines **three related mappings** that connect QIPP workstreams to BNF codes. Each serves a different purpose.

#### Mapping 1: Opportunity Discovery — `WORKSTREAM_MAPPINGS`

**File:** `backend/app/services/opportunity_discovery.py` (lines 32-113)
**Purpose:** Drive the core opportunity discovery algorithm — identify expensive prescribing patterns and their cheaper alternatives.

| Workstream | Therapeutic Area | Expensive BNF Prefix | Target BNF Prefix | Description | Expected Switch Rate |
|-----------|-----------------|---------------------|-------------------|-------------|---------------------|
| **STATINS** | Cardiovascular | `0212000B0AA` | `0212000B0` | Switch branded Atorvastatin to generic | 85% |
| **DOACs** | Cardiovascular | `0208020Z0` | `0208020X0` | Review DOAC prescribing — prefer Edoxaban/Apixaban | 65% |
| **SGLT2** | Diabetes | `0601023AW` | `0601023AV` | Switch Canagliflozin to Dapagliflozin | 70% |
| **DPP4** | Diabetes | `0601023AH` | `0601023AG` | Switch expensive Gliptins to Alogliptin | 80% |
| **PPI** | Gastroenterology | `0103050P0` | `0103050L0` | Switch Esomeprazole/Pantoprazole to Lansoprazole | 90% |
| **ASTHMA_INHALERS** | Respiratory | `0302000C0` | `0302000C0AA` | Switch branded ICS inhalers to generic | 60% |
| **GABAPENTINOIDS** | Pain / Neurology | `0408010AE` | `0408010AE` | Switch branded Lyrica to generic Pregabalin | 85% |
| **ANTIDEPRESSANTS** | Mental Health | `0403030E0` | `0403030D0` | Switch Escitalopram to Citalopram/Sertraline | 55% |
| **GLP1** | Diabetes | `0601023R0` | `0601023T0` | Review GLP1 prescribing cost-effectiveness | 40% |
| **COPD_INHALERS** | Respiratory | `0301040` | `0301040` | Switch LAMA/LABA inhalers to formulary preferred | 50% |

**How it's used in the algorithm:**

```python
for mapping in WORKSTREAM_MAPPINGS:
    expensive_prefix = mapping["expensive_bnf_prefix"]

    # 1. Calculate national average unit cost for expensive drugs
    national_avg = SELECT AVG(actual_cost / items)
                   WHERE bnf_code.startswith(expensive_prefix)

    # 2. Find practices spending >20% above average
    outliers = SELECT practice_ods_code, unit_cost
               WHERE bnf_code.startswith(expensive_prefix)
               HAVING unit_cost > national_avg * 1.2

    # 3. Calculate savings potential per practice
    annual_saving = (unit_cost - national_avg) * total_items

    # 4. Create opportunity with BNF codes
    opportunity = {
        "current_expensive_bnf": expensive_prefix,  # e.g., "0212000B0AA"
        "target_cheap_bnf": mapping["target_bnf_prefix"],  # e.g., "0212000B0"
        ...
    }
```

#### Mapping 2: OpenPrescribing API Queries — `QIPP_WORKSTREAM_QUERIES`

**File:** `backend/app/services/openprescribing_service.py` (lines 68-74)
**Purpose:** Build the BNF code query parameter for the OpenPrescribing `/bnf_code/` and `/spending_by_org/` endpoints.

| Workstream | BNF Prefix | BNF Section Name |
|-----------|-----------|------------------|
| `DPP4` | `0601022` | Dipeptidylpeptidase-4 inhibitors |
| `SGLT2` | `0601023` | Sodium-glucose co-transporter-2 inhibitors |
| `STATINS` | `0212000` | Lipid-regulating drugs |
| `ACE` | `0205051` | ACE inhibitors |
| `BETA_BLOCKERS` | `0204000` | Beta-adrenoceptor blocking drugs |

These are **section-level** prefixes (7 digits) used for API queries, while `WORKSTREAM_MAPPINGS` uses **chemical-level** prefixes (9-11 digits) for more precise matching.

#### Mapping 3: Register Enrichment — `WORKSTREAM_BNF_MAP`

**File:** `backend/app/routers/opportunities.py` (lines 1314-1381)
**Purpose:** Map workstreams to BNF section codes and target drug names for the Opportunity Register (spreadsheet view) and Drug Tariff price enrichment.

| Workstream | BNF Section | Target BNF | Target Drug Name | Chapter |
|-----------|------------|-----------|-----------------|---------|
| `STATINS` | `0212000` | `0212000Y0` | Atorvastatin | 02 |
| `DOACs` | `0208020` | `0208020Z0` | Edoxaban | 02 |
| `SGLT2` | `0601023` | `0601023AD` | Dapagliflozin | 06 |
| `DPP4` | `0601022` | `0601022B0` | Alogliptin | 06 |
| `GLP1` | `0601023` | `0601023AH` | Semaglutide | 06 |
| `PPI` | `0103050` | `0103050P0` | Lansoprazole / Omeprazole (generic) | 01 |
| `ASTHMA_INHALERS` | `0301011` | `0301011AB` | Beclometasone (Clenil Modulite) | 03 |
| `COPD_INHALERS` | `0301040` | `0301040R0` | Formulary LAMA/LABA/ICS | 03 |
| `ANTIDEPRESSANTS` | `0403030` | `0403030D0` | Sertraline (generic) | 04 |
| `GABAPENTINOIDS` | `0408010` | `0408010AE` | Pregabalin (generic) | 04 |
| `DESOGESTREL` | `0703010` | `0703010BB` | Desogestrel (generic) | 07 |

**How it's used for tariff enrichment:**

```python
for ws in workstreams_needed:
    ws_map = WORKSTREAM_BNF_MAP[ws]
    bnf_section = ws_map["bnf_section"]    # e.g., "0212000"
    target_bnf = ws_map["target_bnf"]      # e.g., "0212000Y0"

    # Find most expensive drug in the BNF section (highest price per unit)
    expensive = TariffPriceDocument.find(
        {"product": {"$regex": f"^{bnf_section}"}},
    ).sort("price_per_unit", -1).limit(3)

    # Find cheapest target drug (lowest price per unit)
    target = TariffPriceDocument.find(
        {"product": {"$regex": f"^{target_bnf}"}},
    ).sort("price_per_unit", 1).limit(3)

    # Inject into register row:
    item["expensive_drug_name"] = expensive.vmpp
    item["expensive_unit_cost"] = expensive.price_per_unit
    item["cheap_drug_name"]     = target.vmpp
    item["cheap_unit_cost"]     = target.price_per_unit
    item["unit_saving"]         = expensive_unit_cost - cheap_unit_cost
```

#### Mapping 4: Therapeutic Area Classification — `THERAPEUTIC_AREA_MAP`

**File:** `backend/app/services/openprescribing_service.py` (lines 472-483)

| Workstream | Therapeutic Area |
|-----------|-----------------|
| STATINS | Cardiovascular |
| DOACs | Cardiovascular |
| SGLT2 | Endocrine/Diabetes |
| DPP4 | Endocrine/Diabetes |
| GLP1 | Endocrine/Diabetes |
| PPI | Gastro-Intestinal |
| ASTHMA_INHALERS | Respiratory |
| COPD_INHALERS | Respiratory |
| ANTIDEPRESSANTS | CNS/Mental Health |
| GABAPENTINOIDS | CNS/Pain |

#### Mapping 5: Measure ID → Workstream — `WORKSTREAM_MAPPINGS` (OpenPrescribing)

**File:** `backend/app/services/openprescribing_service.py` (lines 486-497)
**Purpose:** Map OpenPrescribing quality measure IDs to QIPP workstreams for the measure-based opportunity generation engine.

| Measure ID | Workstream | Target Drug |
|-----------|-----------|-------------|
| `statin_intensity` | STATINS | Atorvastatin (Generic) |
| `doac` | DOACs | Edoxaban |
| `sglt2` | SGLT2 | Dapagliflozin |
| `dpp4` | DPP4 | Alogliptin |
| `ppi` | PPI | Lansoprazole |
| `asthma` | ASTHMA_INHALERS | Clenil Modulite |
| `copd` | COPD_INHALERS | Formulary Trimbow/Trelegy |
| `antidepressant` | ANTIDEPRESSANTS | Sertraline |
| `pregabalin` | GABAPENTINOIDS | Pregabalin (Generic) |
| `glp1` | GLP1 | Semaglutide/Dulaglutide optimization |

---

### 13.5 BNF Codes in Opportunity Discovery — Full Algorithm

**File:** `backend/app/services/opportunity_discovery.py`

The `OpportunityDiscoveryEngine` uses BNF codes in **five detection methods**:

#### Method 1: OpenPrescribing Outlier Detection

```
Input:  WORKSTREAM_MAPPINGS[].expensive_bnf_prefix
Query:  SELECT practice_ods_code, AVG(actual_cost / items) AS unit_cost
        FROM prescribing_records
        WHERE bnf_code LIKE '{expensive_prefix}%'
        GROUP BY practice_ods_code
        HAVING unit_cost > national_average * 1.2

Output: Opportunities where a practice pays >20% above average for expensive drugs
```

- Uses `PrescribingRecord.bnf_code.startswith(expensive_prefix)` (SQLAlchemy `startswith`)
- Minimum saving threshold: £500 per practice
- Source tag: `openprescribing_outlier`

#### Method 2: Drug Tariff Price Change Detection

```
Input:  WORKSTREAM_MAPPINGS[].expensive_bnf_prefix + target_bnf_prefix
Query:  Compare avg tariff price for expensive vs target across latest 2 periods
        WHERE bnf_code LIKE '{prefix}%'

Output: Opportunities where price differential widened by >10%
```

- Compares `DrugTariffPrice` records using BNF prefix matching
- Calculates price stability score from period-over-period variance
- Source tag: `tariff_price_change`

#### Method 3: Price Concession Detection

```
Input:  All active price concessions from DrugTariffPrice.is_concession == True
Match:  Check if concession BNF code matches any WORKSTREAM_MAPPINGS expensive_bnf_prefix
        using bnf_code.startswith(prefix) OR prefix.startswith(bnf_code)

Output: Time-sensitive opportunities where concession increases/decreases savings
```

- Bidirectional prefix matching: checks if the concession BNF is within the workstream prefix, OR vice versa
- Source tag: `price_concession`

#### Method 4: Formulary Alignment Check

```
Input:  WORKSTREAM_MAPPINGS[].target_bnf_prefix
Query:  SELECT * FROM formulary_entries
        WHERE bnf_code LIKE '{target_prefix}%'
        AND tenant_id = {tenant}

Output: Boolean — whether the target drug is on the local ICB formulary
```

- Uses `FormularyEntry.bnf_code.startswith(target_prefix)` for hierarchical matching
- Formulary alignment is a scoring factor: aligned = higher composite score

#### Method 5: ePACT2 Data Ingestion

Same prefix-matching logic on ePACT2 imported prescribing data (CSV uploads from NHS BSA).

#### De-duplication

After all five methods run, opportunities are de-duplicated:

```python
Key: (practice_ods_code, workstream, current_expensive_bnf, target_cheap_bnf)
Rule: Keep the opportunity with the highest annual_saving_gbp
```

This prevents duplicate opportunities for the same drug pair at the same practice from different detection methods.

---

### 13.6 BNF Codes in MongoDB Storage

#### OpportunityDocument Fields

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `current_expensive_bnf` | str | `"0212000B0AA"` | BNF prefix of the expensive drug being switched FROM |
| `target_cheap_bnf` | str | `"0212000B0"` | BNF prefix of the cheaper alternative |
| `bnf_section_code` | str | `"0212000"` | BNF section for OpenPrescribing spending lookup |
| `target_bnf_code` | str | `"0212000Y0"` | Specific target drug BNF code (from WORKSTREAM_BNF_MAP) |
| `bnf_chapter` | str | `"02"` | BNF chapter (first 2 digits) — used for register display |
| `spending_items[].bnf_code` | str | `"0212000B0AAABAB"` | Full 15-char presentation code in spending breakdown |
| `spending_items[].bnf_name` | str | `"Atorvastatin 20mg tabs"` | Human-readable presentation name |

#### MedicationDocument Fields

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `bnf_code` | str | `"0212000B0AAABAB"` | Full 15-char presentation code (primary key) |
| `bnf_chapter` | str | `"02"` | First 2 digits — chapter |
| `bnf_section` | str | `"0212"` | First 4 digits — section |
| `bnf_paragraph` | str | `"021200"` | First 6 digits — paragraph |
| `chemical_substance` | str | `"0212000B0"` | First 9 digits — chemical |
| `workstream` | enum | `"STATINS"` | Mapped QIPP workstream |

#### DrugClassDocument (BNF Hierarchy Navigation)

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `bnf_id` | str | `"0212"` | BNF code at this hierarchy level |
| `level` | str | `"section"` | chapter / section / paragraph / subpar |
| `parent_id` | str | `"02"` | Parent code (chapter for sections, section for paragraphs) |
| `name` | str | `"Lipid-Regulating Drugs"` | Human-readable name |

This enables the frontend to navigate: **Chapters → Sections → Paragraphs → Drugs**

---

### 13.7 BNF Code Validation

**File:** `backend/app/ai/parsers/code_mapper.py`

When the AI clinical search generates BNF codes, they are validated against a known section list:

```python
_KNOWN_BNF_SECTIONS = [
    # Gastro-Intestinal (Chapter 01)
    "0101", "0102", "0103",

    # Cardiovascular (Chapter 02)
    "0201", "0202", "0204", "0205", "0206", "0208", "0209", "0212",

    # Respiratory (Chapter 03)
    "0301", "0302", "0303",

    # Central Nervous System (Chapter 04)
    "0401", "0402", "0403", "0407", "0408", "0409", "0410", "0411",

    # Endocrine (Chapter 06)
    "0601", "0602", "0603", "0604", "0605",
]

def validate_bnf(code: str) -> CodeValidation:
    section = code[:4]                    # Extract first 4 chars
    valid = section in _KNOWN_BNF_SECTIONS
    return CodeValidation(
        code=code, system="bnf",
        display_term=f"BNF section {section}",
        valid=valid,
    )
```

**Important:** This is a lightweight seed cache. In production, this would query the NHS TRUD SNOMED CT terminology server for full validation.

The `validate_codes_in_rule_set()` function validates ALL BNF codes in an AI-generated rule set:

```python
def validate_codes_in_rule_set(raw: dict) -> list[CodeValidation]:
    results = []
    for criteria_list_key in ("inclusion_criteria", "exclusion_criteria"):
        for criterion in raw.get(criteria_list_key, []):
            for bc in criterion.get("bnf_codes", []):
                results.append(validate_bnf(bc))
    return results
```

Unverified codes are flagged for manual pharmacist review before the rule set can be approved.

---

### 13.8 BNF Codes in Clinical Safety — Medication History Checks

**File:** `backend/app/routers/clinical_extensions.py`

Before switching a patient, the system checks if they were **previously prescribed** the target drug and stopped:

```python
# Extract chemical-level prefix (9 digits) for matching
target_bnf_prefix = data.get("target_drug_bnf", "")[:9]

# Check each medication in patient's history
for item in patient.current_medications:
    item_bnf = (item.get("bnf_code", "") or "")[:9]  # Compare at chemical level
    is_match = target_bnf_prefix and item_bnf == target_bnf_prefix

    if is_match and item.get("stopped"):
        # Patient was previously on this drug and stopped
        # Check discontinuation reason (adverse reaction, intolerance, etc.)
        # Flag for pharmacist review before re-prescribing
```

This uses **chemical-level matching** (9 digits) — not full presentation matching — because a patient who had an adverse reaction to Atorvastatin 20mg tablets should also be flagged for Atorvastatin 40mg capsules (same chemical, different presentation).

---

### 13.9 BNF Codes in Drug Tariff Price Lookups

#### OpenPrescribing Tariff (CSV)

The Drug Tariff CSV from OpenPrescribing does **not** use BNF codes directly — it uses VMPP IDs (from the NHS dm+d system). The system matches tariff prices to opportunities through workstream-based lookups:

```python
# In opportunities.py — enrich_opportunities_with_drug_details()

for ws in workstreams_needed:
    ws_map = WORKSTREAM_BNF_MAP[ws]
    bnf_section = ws_map["bnf_section"]    # e.g., "0212000"

    # MongoDB regex query: find tariff entries matching BNF section
    expensive_docs = TariffPriceDocument.find(
        {"product": {"$regex": f"^{bnf_section}"}},
    ).sort("price_per_unit", -1)

    # → Returns most expensive drug in the section
    # → Used to calculate unit_saving = expensive - cheap
```

#### PostgreSQL Drug Tariff Prices

The `DrugTariffPrice` model in PostgreSQL stores BNF codes directly:

```python
class DrugTariffPrice(Base):
    bnf_code: str       # BNF code (indexed)
    drug_name: str
    price_pence: int    # Reimbursement price in pence
    category: str       # "Category M", "Category A", "Category C", "Price Concession"
    is_concession: bool
    period: str         # YYYY-MM
```

Queries use `bnf_code.startswith(prefix)` for hierarchical tariff lookups:

```sql
SELECT AVG(price_pence)
FROM drug_tariff_prices
WHERE bnf_code LIKE '0212000B0%'    -- All Atorvastatin presentations
  AND period = '2026-02'
  AND is_concession = FALSE
```

---

### 13.10 BNF Codes in Spending Data Enrichment

When the "Enrich" button is clicked on the Opportunity Register, the system:

1. **Looks up** the opportunity's workstream in `WORKSTREAM_BNF_MAP`
2. **Gets** the `bnf_section` (e.g., `"0212000"` for STATINS)
3. **Calls** OpenPrescribing `/spending_by_org/?code={bnf_section}&org_type={level}&org={ods_code}`
4. **Receives** per-presentation spending data with full 15-char BNF codes
5. **Stores** each as a `SpendingLineItem`:

```python
SpendingLineItem(
    bnf_code="0212000B0AAABAB",        # Full presentation code
    bnf_name="Atorvastatin 20mg tabs",  # Human-readable
    items=456,                          # Prescription items
    quantity=12768,                     # Total quantity
    actual_cost=3456.78,               # Cost in GBP
    unit_cost=7.58,                    # Unit cost from tariff
    date="2025-12-01",                 # Period
)
```

6. **Calculates** derived fields:
   - `total_items` = sum of all line items
   - `total_actual_cost` = sum of all costs
   - `estimated_annual_cost` = annualized cost
   - `pct_saving` = (expensive_unit_cost - cheap_unit_cost) / expensive_unit_cost
   - `avg_saving_per_item` = unit_saving * average quantity per item

---

### 13.11 BNF Codes in CSV Import & Bulk Loading

**File:** `backend/load_opportunities_mongo.py`

When importing opportunities from CSV, workstreams are mapped from BNF codes using a dual strategy:

```python
def map_workstream(bnf_code: str, name: str) -> str:
    name_lower = name.lower()

    # Strategy 1: Drug name pattern matching (primary — more reliable)
    if "dapagliflozin" in name_lower: return "SGLT2"
    if "atorvastatin" in name_lower:  return "STATINS"
    if "edoxaban" in name_lower:      return "DOACs"
    if "alogliptin" in name_lower:    return "DPP4"
    if "lansoprazole" in name_lower:  return "PPI"
    if "pregabalin" in name_lower:    return "GABAPENTINOIDS"
    if "sertraline" in name_lower:    return "ANTIDEPRESSANTS"
    if "semaglutide" in name_lower:   return "GLP1"
    # ... etc

    # Strategy 2: BNF chapter-level fallback (when drug name is ambiguous)
    if bnf_code.startswith("02"): return "Cardiovascular"
    if bnf_code.startswith("06"): return "Endocrine/Diabetes"
    if bnf_code.startswith("01"): return "Gastro-Intestinal"
    if bnf_code.startswith("03"): return "Respiratory"
    if bnf_code.startswith("04"): return "CNS/Mental Health"

    return "Other"
```

---

### 13.12 BNF Codes in the Frontend

The frontend does **not** parse or decompose BNF codes. All BNF processing happens server-side. The frontend receives and displays:

- `current_expensive_bnf` — displayed in the Opportunity Register as the "Current Drug" code
- `target_cheap_bnf` — displayed as the "Target Drug" code
- `bnf_section_code` — used for register grouping
- `bnf_chapter` — used for chapter-level filtering
- Drug names (`expensive_drug_name`, `cheap_drug_name`) — resolved server-side from BNF codes via tariff lookup

---

### 13.13 BNF Code Quick Reference — All Codes Used in QIPP

#### Statins (Chapter 02, Section 0212)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0212000` | Lipid-regulating drugs (section) | OpenPrescribing query prefix |
| `0212000B0` | Atorvastatin (chemical) | Target: generic Atorvastatin |
| `0212000B0AA` | Atorvastatin branded product | Expensive: branded Atorvastatin |
| `0212000Y0` | Atorvastatin (register target code) | Register enrichment lookup |

#### DOACs (Chapter 02, Section 0208)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0208020` | DOACs (section) | Section-level lookup |
| `0208020Z0` | Rivaroxaban (expensive DOAC) | Expensive: Rivaroxaban |
| `0208020X0` | Edoxaban / Apixaban | Target: preferred DOAC |

#### SGLT2 Inhibitors (Chapter 06, Section 0601023)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0601023` | SGLT2 inhibitors (section) | OpenPrescribing query prefix |
| `0601023AW` | Canagliflozin | Expensive: Canagliflozin |
| `0601023AV` | Dapagliflozin | Target: Dapagliflozin |
| `0601023AD` | Dapagliflozin (register code) | Register enrichment target |

#### DPP4 Inhibitors (Chapter 06, Section 0601022)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0601022` | DPP4 inhibitors (section) | OpenPrescribing query prefix |
| `0601023AH` | Expensive Gliptins | Expensive: Sitagliptin etc. |
| `0601023AG` | Alogliptin | Target: Alogliptin |
| `0601022B0` | Alogliptin (register code) | Register enrichment target |

#### GLP1 Agonists (Chapter 06, Section 0601023)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0601023R0` | Expensive GLP1 | Expensive: Exenatide etc. |
| `0601023T0` | Semaglutide | Target: Semaglutide/Dulaglutide |
| `0601023AH` | Semaglutide (register code) | Register enrichment target |

#### PPIs (Chapter 01, Section 0103050)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0103050` | PPIs (section) | Section-level lookup |
| `0103050P0` | Esomeprazole / Pantoprazole | Expensive: branded PPIs |
| `0103050L0` | Lansoprazole | Target: generic Lansoprazole |

#### Asthma Inhalers (Chapter 03, Section 0302)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0301011` | ICS inhalers (section) | Section-level lookup |
| `0302000C0` | Branded ICS inhalers | Expensive: branded inhalers |
| `0302000C0AA` | Generic ICS inhalers | Target: generic equivalent |
| `0301011AB` | Beclometasone (Clenil) | Register target: Clenil Modulite |

#### COPD Inhalers (Chapter 03, Section 0301040)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0301040` | LAMA/LABA inhalers (section) | Both expensive and target prefix |
| `0301040R0` | Formulary LAMA/LABA/ICS | Register target: Trimbow/Trelegy |

#### Antidepressants (Chapter 04, Section 0403030)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0403030` | SSRIs (section) | Section-level lookup |
| `0403030E0` | Escitalopram | Expensive: Escitalopram |
| `0403030D0` | Sertraline | Target: generic Sertraline |

#### Gabapentinoids (Chapter 04, Section 0408010)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0408010` | Antiepileptics (section) | Section-level lookup |
| `0408010AE` | Pregabalin (branded Lyrica) | Expensive: branded Pregabalin |
| `0408010AE` | Pregabalin (generic) | Target: same chemical, generic presentation |

#### ACE Inhibitors & Beta-Blockers (Additional Workstreams)

| BNF Code | Drug | Workstream |
|----------|------|-----------|
| `0205051` | ACE inhibitors | ACE |
| `0204000` | Beta-blockers | BETA_BLOCKERS |

#### Desogestrel (Chapter 07, Section 0703010)

| BNF Code | Drug | Role in QIPP |
|----------|------|-------------|
| `0703010` | Progestogen-only contraceptives | Section-level lookup |
| `0703010BB` | Desogestrel (generic) | Register target |

---

### 13.14 Summary: BNF Code Usage Across the System

| Component | BNF Usage | Prefix Length | Pattern |
|-----------|----------|---------------|---------|
| **Opportunity Discovery** | Match expensive/target drugs | 7-11 chars | `startswith()` on PostgreSQL |
| **OpenPrescribing API queries** | Build `?code=` parameter | 7 chars | Section-level prefix |
| **Tariff price lookups** | Find drug prices | 7-9 chars | `$regex: ^prefix` on MongoDB |
| **Spending enrichment** | Fetch per-presentation data | 7 chars | Section-level for API call |
| **Medication catalog** | Store/index drugs | 15 chars | Full presentation code |
| **BNF hierarchy navigation** | Chapters → Sections → Drugs | 2-15 chars | `DrugClassDocument` tree |
| **Clinical safety checks** | Patient medication history | 9 chars | Chemical-level comparison |
| **AI code validation** | Validate AI-generated codes | 4 chars | Section prefix lookup |
| **CSV import** | Auto-classify workstream | 2 chars | Chapter-level fallback |
| **De-duplication** | Unique opportunity key | Variable | Exact match on expensive + target pair |
| **Register display** | Show BNF codes in spreadsheet | Variable | Direct display from stored fields |
| **Formulary alignment** | Check if target is on formulary | 9 chars | Chemical-level prefix match |

---

> **End of QIPP System Documentation**
> This document covers the complete system architecture, all 12 external API integrations with full endpoint documentation, all database models (44 PostgreSQL + 12 MongoDB), 80+ Pydantic schemas, background task scheduling, middleware stack, operational reference, and comprehensive BNF code system documentation.
