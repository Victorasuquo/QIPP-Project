# QIPP MongoDB Database Documentation

This document provides a comprehensive overview of the `qipp_patients` MongoDB database. It details every collection, its schema, data types, purpose, and includes real sample entries extracted directly from the database.

---

## High-Level Architecture

The MongoDB database (`qipp_patients`) is used primarily for storing high-volume, document-oriented clinical data that doesn't fit well into the core PostgreSQL relational database. This includes:

- **Patient Records & Analytics**: Raw patient data, conditions, medications, and dynamic risk scores.
- **Opportunities Pipeline**: The AI-identified and ranked cost-saving switch opportunities.
- **Drug Tariff & Medication Data**: Live drug pricing from the NHS Drug Tariff (over 590,000 records).
- **Background Sync Logs**: Audit logs for the various Celery background tasks that sync external data (Tariff, OpenPrescribing, ePACT2).

---

## Collections Breakdown

### 1. `opportunities`
**Document Count:** 1,198
**Purpose:** Stores the core cost-saving interventions identified by the `OpportunityDiscoveryEngine`. These are the items that appear on the Opportunity Workspace and Sub-ICB/PCN dashboards.

#### Schema
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Internal MongoDB identifier. |
| `opportunity_id` | str | UUID linking back to tracking/Postgres structures if needed. |
| `org_level` | str | Level of the organisation (e.g., `icb`, `sub_icb`, `pcn`, `practice`). |
| `practice_ods_code` | str / null | The practice ODS code if applicable. |
| `pcn_ods_code` | str / null | The PCN ODS code if applicable. |
| `sub_icb_ods_code` | str / null | The Sub-ICB ODS code if applicable. |
| `icb_id` | str | The Tenant ID (UUID format) of the ICB. |
| `workstream` | str | The category of the switch. |
| `description` | str | Human-readable description of the switch. |
| `estimated_annual_savings` | float | Calculated cash value of the opportunity over 12 months. |
| `patients_affected` | int | Number of eligible patients in the cohort. |
| `current_expensive_bnf` | str | The BNF code or label of the current expensive drug. |
| `target_cheap_bnf` | str | The BNF code or label of the cheaper alternative drug. |
| `status` | str | Current state in the pipeline (e.g., `IDENTIFIED`). |
| `priority_rank` | int | Priority tier ranking. |
| `effort_reward_score` | float | Composite score evaluating cash value vs. implementation effort. |
| `therapeutic_area` | str | The clinical category (e.g., `Low-Priority Prescribing`, `Diabetes`). |
| `created_at` / `updated_at` | Date | Audit timestamps. |

#### Sample Document
```json
{
  "_id": "69b0361d6fafb1347d8bb260",
  "opportunity_id": "484cac2c-fe0b-4dc3-8f7f-33e3bc2efcec",
  "org_level": "icb",
  "icb_id": "f3eedabc-dd89-42b2-8800-ea6834ad11e7",
  "workstream": "LOW_PRIORITY",
  "description": "Low-priority: bath/shower emollients — should not routinely prescribe",
  "estimated_annual_savings": 129472.43,
  "patients_affected": 1641,
  "current_expensive_bnf": "Measure: lpbathshoweremollients (percentile: 88th)",
  "target_cheap_bnf": "Leave-on emollients / patient purchase",
  "status": "IDENTIFIED",
  "effort_reward_score": 78.9,
  "priority_rank": 3,
  "therapeutic_area": "Low-Priority Prescribing"
}
```

---

### 2. `tariff_prices`
**Document Count:** 590,817
**Purpose:** A massive collection storing historic and live NHS Drug Tariff pricing data. This is used to dynamically calculate the `cost_per_unit` of drugs for opportunity identification.

#### Schema
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Internal MongoDB identifier. |
| `vmpp_id` | str | Virtual Medicinal Product Pack identifier (dm+d). |
| `vmpp` | str | Full human-readable name of the medicinal product pack. |
| `product` | str | The BNF Code mapping for the product. |
| `tariff_category` | str | e.g., `Part VIIIA Category A`, `Part VIIIA Category M`. |
| `price_pence` | int | The official tariff price in pence. |
| `price_pounds` | float | The official tariff price converted to pounds (£). |
| `pack_size` | float | Number of units in the pack. |
| `price_per_unit` | float | Calculated price per individual pill/dose (`price_pounds` / `pack_size`). |
| `date` | str | The effective date/month of the tariff (e.g., `2010-03-01`). |
| `concession` | bool | Whether a Price Concession is active for this pack. |
| `fetched_at` | Date | When the backend last synced this record. |
| `data_source` | str | Source of the sync. |

#### Sample Document
```json
{
  "_id": "699eabefc648c0463718084c",
  "vmpp_id": "943511000001100",
  "vmpp": "Acebutolol 400mg tablets 28 tablet",
  "product": "0204000C0AAADAD",
  "tariff_category": "Part VIIIA Category A",
  "price_pence": 1880,
  "pack_size": 28.0,
  "date": "2010-03-01",
  "concession": false,
  "price_pounds": 18.8,
  "price_per_unit": 0.6714,
  "data_source": "sync from API source"
}
```

---

### 3. `patients`
**Document Count:** 813
**Purpose:** Stores rich, document-oriented clinical profiles for patients, including their conditions, current medications, contraindications, and switch eligibility status. 

#### Schema
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Internal identifier. |
| `nhs_number` | str | The 10-digit NHS patient identifier. |
| `practice_ods_code` | str | The ODS code of the GP practice the patient belongs to. |
| `first_name` / `last_name` | str | Patient demographics. |
| `date_of_birth` | Date | Patient DOB. |
| `age` | int | Computed age. |
| `gender` | str | Patient gender. |
| `renal_function_egfr` | int | Clinical marker (eGFR) used for switch safety checks. |
| `hba1c` / `systolic_bp` / `weight_kg` | float / int | Clinical biometrics. |
| `smoking_status` / `diabetes_type` | str | Clinical context flags. |
| `medications` | Array[Object] | List of currently prescribed BNF drugs (`bnf_code`, `name`, `dose`, `cost_per_unit`). |
| `conditions` | Array[Object] | SNOMED/ICD-10 clinical conditions. |
| `contraindications` | Array[str] | Known allergies or clinical warnings blocking a switch. |
| `risk_level` / `risk_score` | str / float | Calculated patient risk tier. |
| `is_switch_eligible` | bool | True if the backend pipeline cleared them for a medication switch. |
| `estimated_annual_savings` | float | Potential saving if this individual patient is switched. |
| `workstream` | str | The opportunity workstream they belong to (e.g., `DPP4`). |
| `eligibility_reasons` | Array[str] | Ex: "Adequate renal function (eGFR 60)". |

#### Sample Document
```json
{
  "_id": "69986ba181baa9a3d5f522a3",
  "nhs_number": "3301887481",
  "practice_ods_code": "G95614",
  "first_name": "Angela",
  "last_name": "Lloyd",
  "age": 62,
  "renal_function_egfr": 60,
  "hba1c": 44.5,
  "medications": [
    {
      "bnf_code": "0601022B0AAABAB",
      "name": "Sitagliptin 50mg tablets",
      "dose": "25mg OD",
      "is_current": true,
      "cost_per_unit": 33.26
    }
  ],
  "conditions": [{"name": "Obesity (E66)"}, {"name": "Type 2 Diabetes Mellitus (E11)"}],
  "contraindications": ["Hypersensitivity to DPP-4 inhibitors"],
  "risk_level": "low",
  "is_switch_eligible": true,
  "estimated_annual_savings": 302.07,
  "workstream": "DPP4"
}
```

---

### 4. `patient_analytics`
**Document Count:** 812
**Purpose:** Pre-computed risk and financial analytics per patient, designed for rapid dashboard rendering and sorting of action lists.

#### Schema
| Field | Type | Description |
|---|---|---|
| `patient_nhs_number` | str | Link to the `patients` collection. |
| `current_annual_cost` | float | Current total cost of medications per year. |
| `alternative_annual_cost` | float | Simulated cost if all target switches are applied. |
| `potential_savings` | float | The delta (`current - alternative`). |
| `risk_score` | float | The clinical risk score weighting. |
| `eligibility_checks` | Object | Map of boolean flags confirming safety. |

#### Sample Document
```json
{
  "_id": "69986ba281baa9a3d5f522a4",
  "patient_nhs_number": "3301887481",
  "current_annual_cost": 0.0,
  "alternative_annual_cost": 0.0,
  "potential_savings": 302.07,
  "risk_score": 15.0,
  "eligibility_checks": {
    "egfr_ok": true,
    "no_contraindications": true
  }
}
```

---

### 5. `medications`
**Document Count:** 1,356
**Purpose:** Master catalogue of target medications the system is actively tracking.

#### Schema
| Field | Type | Description |
|---|---|---|
| `bnf_code` | str | Standard BNF code (e.g., `0601022B0AAAAAA`). |
| `name` | str | Full generic/brand name. |
| `bnf_chapter` / `bnf_section` | str | Categorization taxonomy. |
| `is_generic` | bool | Identifier for generic vs branded prescribing. |
| `cost_per_unit` | float | Reference standard cost. |
| `workstream` | str | The workstream this drug is evaluated under. |
| `is_active` | bool | Whether the pipeline actively scans for this drug. |

---

### 6. `drug_classes`
**Document Count:** 16
**Purpose:** Hierarchical BNF structure mapping (Chapters, Sections) used to build UI dropdowns and filter therapeutic areas.

#### Sample Document
```json
{
  "_id": "699c7783a514cc7b65d60317",
  "bnf_id": "02",
  "name": "Cardiovascular System",
  "level": "chapter",
  "parent_id": null
}
```

---

### 7. Core Sync Logs
**Purpose:** Audit trailing for the automated data engineering pipelines running in background Celery workers.

* **`sync_logs` (Count: 2):** Tracks patient syncs from external synthetic generators or GP systems.
* **`med_sync_logs` (Count: 50):** Tracks the automated update of target QIPP drugs.
* **`tariff_sync_logs` (Count: 19):** Tracks the massive monthly ingestion of the NHS Drug Tariff CSV files.

#### Sample `sync_logs` Entry
```json
{
  "run_id": "5979a8c9-f741-4f25-bb01-5c37c29df924",
  "trigger": "manual",
  "status": "completed",
  "patients_fetched": 500,
  "patients_created": 500,
  "duration_seconds": 367.51
}
```

---

### Empty Collections (Future Pipeline / Deprecated)
* **`practice_measures`**: Intended for aggregated OpenPrescribing statistical measures (currently unused or cleared).
* **`icb_monthly_reports`**: For persistent storage of generated PDF/HTML monthly reports.
* **`prescriptions`**: Individual prescription event logs (currently folded into the `patients.medications` array for optimization).

---

## Conclusion
The MongoDB setup relies heavily on **denormalization**. Complex data that belongs together (like a patient and their current prescriptions and clinical flags) are stored as nested arrays in a single document. This avoids complex SQL `JOIN`s when loading dashboards and enables the `ScoringEngine` to process thousands of records within milliseconds. The massive `tariff_prices` collection serves as the live lookup table ensuring that every financial calculation on the dashboard reflects the real-world NHS Drug Tariff prices.
