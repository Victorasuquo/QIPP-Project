# QIPP PostgreSQL Database Documentation

This document provides a detailed overview of the core relational database (PostgreSQL via Supabase) used in the QIPP Medicines Optimization platform. It covers all active tables, their schemas, relationships (foreign keys), and sample data.

## Table: `action_sheets`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `workstream` | `character varying` | No | `` |
| `icb_id` | `uuid` | No | `` |
| `created_by_user_id` | `uuid` | No | `` |
| `content` | `jsonb` | Yes | `` |
| `template_version` | `character varying` | Yes | `` |
| `status` | `character varying` | No | `'draft'::character varying` |
| `file_url` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `practice_ods_code` | `character varying` | Yes | `` |

### Relationships
- `created_by_user_id` → `users.id`
- `icb_id` → `icbs.id`

---

## Table: `ai_decision_audit`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `` |
| `tenant_id` | `uuid` | Yes | `` |
| `user_id` | `uuid` | Yes | `` |
| `rule_set_id` | `uuid` | Yes | `` |
| `action` | `character varying` | No | `` |
| `input_summary` | `text` | Yes | `` |
| `output_summary` | `text` | Yes | `` |
| `guardrail_safe` | `boolean` | No | `` |
| `flagged_phrases` | `jsonb` | Yes | `` |
| `human_action` | `character varying` | Yes | `` |
| `human_notes` | `text` | Yes | `` |
| `endpoint` | `character varying` | Yes | `` |
| `extra` | `jsonb` | Yes | `` |
| `created_at` | `timestamp with time zone` | No | `` |

### Relationships
- `rule_set_id` → `ai_rule_sets.id`
- `tenant_id` → `tenants.id`
- `user_id` → `users.id`

---

## Table: `ai_rule_sets`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `` |
| `tenant_id` | `uuid` | No | `` |
| `created_by_user_id` | `uuid` | No | `` |
| `approved_by_user_id` | `uuid` | Yes | `` |
| `query_text` | `text` | No | `` |
| `rule_set_json` | `jsonb` | No | `` |
| `transpiled_query` | `text` | Yes | `` |
| `target_system` | `character varying` | No | `` |
| `version` | `integer` | No | `` |
| `parent_id` | `uuid` | Yes | `` |
| `status` | `character varying` | No | `` |
| `rejection_reason` | `text` | Yes | `` |
| `therapeutic_area` | `character varying` | Yes | `` |
| `estimated_patient_count` | `integer` | Yes | `` |
| `search_file_content` | `text` | Yes | `` |
| `ai_confidence` | `double precision` | Yes | `` |
| `safety_warnings` | `jsonb` | Yes | `` |
| `requires_manual_review_flags` | `jsonb` | Yes | `` |
| `guardrail_safe` | `boolean` | No | `` |
| `flagged_phrases` | `jsonb` | Yes | `` |
| `created_at` | `timestamp with time zone` | No | `` |
| `approved_at` | `timestamp with time zone` | Yes | `` |
| `updated_at` | `timestamp with time zone` | No | `` |

### Relationships
- `approved_by_user_id` → `users.id`
- `created_by_user_id` → `users.id`
- `parent_id` → `ai_rule_sets.id`
- `tenant_id` → `tenants.id`

---

## Table: `audit_logs`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `user_id` | `uuid` | Yes | `` |
| `action` | `character varying` | No | `` |
| `entity_type` | `character varying` | No | `` |
| `entity_id` | `uuid` | Yes | `` |
| `old_values` | `jsonb` | Yes | `` |
| `new_values` | `jsonb` | Yes | `` |
| `ip_address` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `user_id` → `users.id`

---

## Table: `data_freshness`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `source_name` | `character varying` | No | `` |
| `last_updated` | `timestamp with time zone` | Yes | `` |
| `last_attempted` | `timestamp with time zone` | Yes | `` |
| `next_expected` | `timestamp with time zone` | Yes | `` |
| `record_count` | `integer` | No | `` |
| `status` | `character varying` | No | `'unknown'::character varying` |
| `last_error` | `text` | Yes | `` |
| `metadata_extra` | `jsonb` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

---

## Table: `dmd_products`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `dmd_code` | `character varying` | No | `` |
| `name` | `character varying` | No | `` |
| `bnf_code` | `character varying` | Yes | `` |
| `product_type` | `character varying` | No | `` |
| `vmp_code` | `character varying` | Yes | `` |
| `form` | `character varying` | Yes | `` |
| `route` | `character varying` | Yes | `` |
| `strength` | `character varying` | Yes | `` |
| `supplier` | `character varying` | Yes | `` |
| `status` | `character varying` | No | `'active'::character varying` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

---

## Table: `drug_tariff_prices`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `drug_name` | `character varying` | No | `` |
| `bnf_code` | `character varying` | No | `` |
| `category` | `character varying` | No | `` |
| `price_pence` | `integer` | No | `` |
| `period` | `character varying` | No | `` |
| `is_concession` | `boolean` | No | `false` |
| `pack_size` | `character varying` | Yes | `` |
| `formulation` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

---

## Table: `email_logs`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | Yes | `` |
| `to_email` | `character varying` | No | `` |
| `from_email` | `character varying` | No | `` |
| `subject` | `character varying` | No | `` |
| `template_name` | `character varying` | Yes | `` |
| `status` | `character varying` | No | `` |
| `provider` | `character varying` | Yes | `` |
| `provider_message_id` | `character varying` | Yes | `` |
| `error_message` | `text` | Yes | `` |
| `event_type` | `character varying` | Yes | `` |
| `metadata_json` | `jsonb` | Yes | `` |
| `sent_at` | `timestamp with time zone` | Yes | `` |
| `delivered_at` | `timestamp with time zone` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `epact_records`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `practice_ods_code` | `character varying` | No | `` |
| `bnf_code` | `character varying` | No | `` |
| `bnf_name` | `character varying` | No | `` |
| `items` | `integer` | No | `` |
| `quantity` | `double precision` | No | `` |
| `actual_cost` | `double precision` | No | `` |
| `nic` | `double precision` | No | `` |
| `formulation` | `character varying` | Yes | `` |
| `strength` | `character varying` | Yes | `` |
| `period` | `character varying` | No | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `formulary_entries`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `drug_name` | `character varying` | No | `` |
| `bnf_code` | `character varying` | Yes | `` |
| `dmd_code` | `character varying` | Yes | `` |
| `snomed_code` | `character varying` | Yes | `` |
| `therapeutic_area` | `character varying` | Yes | `` |
| `formulary_tier` | `integer` | No | `` |
| `preferred_product` | `character varying` | Yes | `` |
| `notes` | `text` | Yes | `` |
| `version` | `integer` | No | `` |
| `status` | `character varying` | No | `'active'::character varying` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `formulary_snapshots`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `version` | `integer` | No | `` |
| `label` | `character varying` | Yes | `` |
| `snapshot_data` | `jsonb` | No | `` |
| `changes_summary` | `jsonb` | Yes | `` |
| `notes` | `text` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `icbs`
**Row Count:** 47

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `name` | `character varying` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `prescribing_budget` | `numeric` | Yes | `` |
| `contact_email` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `address` | `text` | Yes | `` |
| `phone` | `character varying` | Yes | `` |
| `website` | `character varying` | Yes | `` |
| `postcode` | `character varying` | Yes | `` |
| `last_ods_sync` | `timestamp with time zone` | Yes | `` |
| `email_domain` | `character varying` | Yes | `` |

### Sample Record
```json
{
  "name": "Nhs Lancashire And South Cumbria Integrated Care Board",
  "ods_code": "QE1",
  "prescribing_budget": null,
  "contact_email": null,
  "id": "95557472-5bee-41e8-af0d-e97885a581c0",
  "created_at": "2026-03-03T20:08:40.173744+00:00",
  "updated_at": "2026-03-03T20:08:40.173744+00:00",
  "address": "LEVEL 3, CHRIST CHURCH PRECINCT, COUNTY HALL, FISHERGATE HILL, PRESTON, PR1 8XB",
  "phone": null,
  "website": null,
  "postcode": "PR1 8XB",
  "last_ods_sync": "2026-03-03T20:06:54.986744+00:00",
  "email_domain": "lsc.icb.nhs.uk"
}
```

---

## Table: `import_jobs`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `user_id` | `uuid` | No | `` |
| `job_type` | `character varying` | No | `` |
| `status` | `character varying` | No | `'pending'::character varying` |
| `file_name` | `character varying` | Yes | `` |
| `total_records` | `integer` | Yes | `` |
| `processed_records` | `integer` | No | `0` |
| `error_message` | `text` | Yes | `` |
| `completed_at` | `timestamp with time zone` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `user_id` → `users.id`

---

## Table: `interventions`
**Row Count:** 13

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `name` | `character varying` | No | `` |
| `description` | `text` | Yes | `` |
| `therapeutic_area` | `character varying` | Yes | `` |
| `workstream_code` | `character varying` | Yes | `` |
| `current_drug` | `character varying` | No | `` |
| `target_drug` | `character varying` | No | `` |
| `preferred_product` | `character varying` | Yes | `` |
| `current_drug_bnf` | `character varying` | Yes | `` |
| `target_drug_bnf` | `character varying` | Yes | `` |
| `status` | `character varying` | No | `'DRAFT'::character varying` |
| `status_reason` | `text` | Yes | `` |
| `status_changed_at` | `timestamp with time zone` | Yes | `` |
| `status_changed_by` | `character varying` | Yes | `` |
| `forecast_annual_savings` | `double precision` | Yes | `` |
| `realized_savings` | `double precision` | No | `` |
| `switchback_cost` | `double precision` | No | `` |
| `total_eligible_patients` | `integer` | No | `` |
| `patients_switched` | `integer` | No | `` |
| `patients_refused` | `integer` | No | `` |
| `patients_excluded` | `integer` | No | `` |
| `patients_switched_back` | `integer` | No | `` |
| `clinical_rule_set` | `jsonb` | Yes | `` |
| `practice_ods_codes` | `jsonb` | Yes | `` |
| `approved_at` | `timestamp with time zone` | Yes | `` |
| `execution_started_at` | `timestamp with time zone` | Yes | `` |
| `completed_at` | `timestamp with time zone` | Yes | `` |
| `state_history` | `jsonb` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

### Sample Record
```json
{
  "tenant_id": "2dd0b5c9-95c2-4955-91cd-ec338b848957",
  "name": "SGLT2 \u2014 Endocrine/Diabetes (2 practices)",
  "description": "Auto-synced from MongoDB opportunities. Covers 2 practices in Endocrine/Diabetes.",
  "therapeutic_area": "Endocrine/Diabetes",
  "workstream_code": "SGLT2::Endocrine/Diabetes",
  "current_drug": "0601023AGAAABAB",
  "target_drug": "To be determined",
  "preferred_product": null,
  "current_drug_bnf": "0601023AGAAABAB",
  "target_drug_bnf": null,
  "status": "DRAFT",
  "status_reason": null,
  "status_changed_at": null,
  "status_changed_by": null,
  "forecast_annual_savings": 46196.84,
  "realized_savings": 0.0,
  "switchback_cost": 0.0,
  "total_eligible_patients": 250,
  "patients_switched": 0,
  "patients_refused": 0,
  "patients_excluded": 0,
  "patients_switched_back": 0,
  "clinical_rule_set": null,
  "practice_ods_codes": [
    "C85004",
    "Y00411"
  ],
  "approved_at": null,
  "execution_started_at": null,
  "completed_at": null,
  "state_history": [],
  "id": "3cf47c75-5a12-4330-8475-2f0dc58a9bbd",
  "created_at": "2026-03-04T16:50:35.131372+00:00",
  "updated_at": null
}
```

---

## Table: `medications`
**Row Count:** 10

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `bnf_code` | `character varying` | No | `` |
| `name` | `character varying` | No | `` |
| `is_generic` | `boolean` | No | `false` |
| `unit_cost` | `numeric` | Yes | `` |
| `therapeutic_class` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Sample Record
```json
{
  "bnf_code": "0601023B0AAAAAA",
  "name": "Sitagliptin 100mg tablets",
  "is_generic": false,
  "unit_cost": "33.2600",
  "therapeutic_class": "Antidiabetic - DPP-4 Inhibitors",
  "id": "06d51663-2194-4c80-a309-832ac0653129",
  "created_at": "2026-03-03T16:53:09.372048+00:00",
  "updated_at": null
}
```

---

## Table: `notifications`
**Row Count:** 18

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `user_id` | `uuid` | No | `` |
| `title` | `character varying` | No | `` |
| `message` | `character varying` | No | `` |
| `category` | `character varying` | No | `` |
| `is_read` | `boolean` | No | `` |
| `metadata_payload` | `jsonb` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `user_id` → `users.id`

### Sample Record
```json
{
  "user_id": "a6dd793a-8496-48ad-bc67-8c781512852b",
  "title": "New Login Detected",
  "message": "Login to QIPP account on 2026-03-03 17:57",
  "category": "alert",
  "is_read": false,
  "metadata_payload": {
    "event": "login_alert",
    "timestamp": "2026-03-03T17:57:12.240818",
    "ip_address": "Recorded IP"
  },
  "id": "cb7fabf8-5329-47ec-bc86-3df915a6d339",
  "created_at": "2026-03-03T16:57:13.808632+00:00",
  "updated_at": null
}
```

---

## Table: `ods_organisations`
**Row Count:** 9191

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `name` | `character varying` | No | `` |
| `org_type` | `character varying` | No | `` |
| `parent_ods_code` | `character varying` | Yes | `` |
| `status` | `character varying` | No | `'active'::character varying` |
| `nhs_ods_data` | `jsonb` | Yes | `` |
| `address` | `text` | Yes | `` |
| `postcode` | `character varying` | Yes | `` |
| `phone` | `character varying` | Yes | `` |
| `clinical_system` | `character varying` | Yes | `` |
| `last_synced_at` | `timestamp with time zone` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

### Sample Record
```json
{
  "tenant_id": "2dd0b5c9-95c2-4955-91cd-ec338b848957",
  "ods_code": "00N",
  "name": "Nhs North East And North Cumbria Icb - 00N",
  "org_type": "SUB_ICB",
  "parent_ods_code": "QHM",
  "status": "active",
  "nhs_ods_data": null,
  "address": "MONKTON HALL, MONKTON LANE, MONKTON VILLAGE, JARROW",
  "postcode": "NE32 5NN",
  "phone": null,
  "clinical_system": null,
  "last_synced_at": "2026-03-07T16:39:32.088445+00:00",
  "id": "f4a2eaaa-8e62-47d6-9ad9-24528b5dc531",
  "created_at": "2026-03-07T16:39:32.088445+00:00",
  "updated_at": "2026-03-07T16:39:32.088445+00:00"
}
```

---

## Table: `org_email_domains`
**Row Count:** 9136

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `email_domain` | `character varying` | No | `` |
| `org_level` | `character varying` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `org_name` | `character varying` | Yes | `` |
| `icb_ods_code` | `character varying` | Yes | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Sample Record
```json
{
  "id": "94381945-453b-4cc9-bef8-0afcb94e16e9",
  "email_domain": "queenspark.surgery.nhs.uk",
  "org_level": "practice",
  "ods_code": "A81002",
  "org_name": "QUEENS PARK MEDICAL CENTRE",
  "icb_ods_code": "QHM",
  "created_at": "2026-03-07T23:04:34.220365+00:00",
  "updated_at": null
}
```

---

## Table: `patent_expiries`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `bnf_code` | `character varying` | No | `` |
| `drug_name` | `character varying` | No | `` |
| `brand_name` | `character varying` | No | `` |
| `patent_expiry_date` | `date` | Yes | `` |
| `generic_available_date` | `date` | Yes | `` |
| `branded_unit_price_pence` | `integer` | Yes | `` |
| `generic_unit_price_pence` | `integer` | Yes | `` |
| `estimated_price_drop_pct` | `numeric` | Yes | `` |
| `estimated_annual_saving_gbp` | `numeric` | Yes | `` |
| `monitoring_status` | `character varying` | No | `'upcoming'::character varying` |
| `source` | `character varying` | No | `` |
| `notes` | `text` | Yes | `` |
| `tariff_category_before` | `character varying` | Yes | `` |
| `tariff_category_after` | `character varying` | Yes | `` |
| `last_checked` | `timestamp with time zone` | Yes | `` |
| `opportunity_auto_created` | `boolean` | No | `false` |
| `on_watch_list` | `boolean` | No | `false` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

---

## Table: `patient_letters`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `intervention_id` | `uuid` | No | `` |
| `patient_nhs_number` | `character varying` | Yes | `` |
| `patient_name` | `character varying` | No | `` |
| `patient_email` | `character varying` | Yes | `` |
| `current_drug` | `character varying` | No | `` |
| `new_drug` | `character varying` | No | `` |
| `template_name` | `character varying` | No | `` |
| `letter_body_json` | `text` | Yes | `` |
| `pdf_generated` | `boolean` | No | `false` |
| `pdf_generated_at` | `timestamp with time zone` | Yes | `` |
| `email_sent` | `boolean` | No | `false` |
| `email_sent_at` | `timestamp with time zone` | Yes | `` |
| `email_delivery_status` | `character varying` | Yes | `` |
| `email_provider` | `character varying` | Yes | `` |
| `practice_name` | `character varying` | Yes | `` |
| `practice_ods_code` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `intervention_id` → `interventions.id`
- `tenant_id` → `tenants.id`

---

## Table: `patient_worklist_items`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `intervention_id` | `uuid` | No | `` |
| `practice_ods_code` | `character varying` | Yes | `` |
| `patient_id` | `uuid` | Yes | `` |
| `nhs_number` | `character varying` | Yes | `` |
| `patient_name` | `character varying` | No | `` |
| `date_of_birth` | `date` | Yes | `` |
| `current_drug` | `character varying` | No | `` |
| `current_dose` | `character varying` | Yes | `` |
| `target_drug` | `character varying` | No | `` |
| `preferred_product` | `character varying` | Yes | `` |
| `clinical_rationale` | `text` | Yes | `` |
| `is_care_home` | `boolean` | No | `false` |
| `has_renal_impairment` | `boolean` | No | `false` |
| `has_prior_switchback` | `boolean` | No | `false` |
| `has_specialist_instruction` | `boolean` | No | `false` |
| `exclusion_flags_json` | `jsonb` | Yes | `` |
| `status` | `character varying` | No | `'pending'::character varying` |
| `outcome_date` | `date` | Yes | `` |
| `outcome_reason` | `text` | Yes | `` |
| `outcome_read_code` | `character varying` | Yes | `` |
| `new_product_name` | `character varying` | Yes | `` |
| `switchback_date` | `date` | Yes | `` |
| `switchback_reason` | `text` | Yes | `` |
| `switchback_count` | `integer` | No | `0` |
| `letter_sent` | `boolean` | No | `false` |
| `letter_sent_date` | `date` | Yes | `` |
| `letter_language` | `character varying` | Yes | `'en'::character varying` |
| `actioned_by` | `character varying` | Yes | `` |
| `actioned_at` | `timestamp with time zone` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `intervention_id` → `interventions.id`
- `patient_id` → `patients.id`
- `tenant_id` → `tenants.id`

---

## Table: `patients`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `nhs_number` | `character varying` | Yes | `` |
| `practice_id` | `uuid` | No | `` |
| `date_of_birth` | `date` | No | `` |
| `gender` | `character varying` | Yes | `` |
| `current_medication_id` | `uuid` | Yes | `` |
| `current_dose` | `character varying` | Yes | `` |
| `renal_function_egfr` | `integer` | Yes | `` |
| `contraindications` | `jsonb` | Yes | `'[]'::jsonb` |
| `last_review_date` | `date` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `is_deleted` | `boolean` | No | `false` |

### Relationships
- `current_medication_id` → `medications.id`
- `practice_id` → `practices.id`

---

## Table: `pcns`
**Row Count:** 1299

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `name` | `character varying` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `icb_id` | `uuid` | No | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `address` | `text` | Yes | `` |
| `phone` | `character varying` | Yes | `` |
| `postcode` | `character varying` | Yes | `` |
| `last_ods_sync` | `timestamp with time zone` | Yes | `` |
| `sub_icb_ods_code` | `character varying` | Yes | `` |
| `email_domain` | `character varying` | Yes | `` |

### Relationships
- `icb_id` → `icbs.id`

### Sample Record
```json
{
  "name": "Kettering Central Pcn",
  "ods_code": "U05468",
  "icb_id": "e38d403b-7e3e-4d7e-96df-c6f4f3783c7b",
  "id": "3e31597e-3a2d-4a5c-b0ec-ecb2f958d36a",
  "created_at": "2026-03-03T20:08:40.173744+00:00",
  "updated_at": "2026-03-03T20:08:40.173744+00:00",
  "address": null,
  "phone": null,
  "postcode": "NN16 8DN",
  "last_ods_sync": "2026-03-03T20:06:54.986744+00:00",
  "sub_icb_ods_code": "15E",
  "email_domain": "ketteringcentral.pcn.nhs.uk"
}
```

---

## Table: `pii_access_logs`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `accessor_id` | `uuid` | No | `` |
| `accessor_role` | `character varying` | No | `` |
| `tenant_id` | `uuid` | No | `` |
| `patient_record_id` | `uuid` | No | `` |
| `action` | `character varying` | No | `` |
| `access_reason` | `character varying` | No | `` |
| `ip_address` | `character varying` | Yes | `` |
| `request_id` | `character varying` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `accessor_id` → `users.id`
- `patient_record_id` → `pii_patient_records.id`
- `tenant_id` → `tenants.id`

---

## Table: `pii_patient_records`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `nhs_number_encrypted` | `text` | No | `` |
| `nhs_number_hash` | `character varying` | No | `` |
| `name_encrypted` | `text` | Yes | `` |
| `date_of_birth_encrypted` | `text` | Yes | `` |
| `practice_ods_code` | `character varying` | No | `` |
| `age_band` | `character varying` | Yes | `` |
| `gender` | `character varying` | Yes | `` |
| `current_medications` | `jsonb` | Yes | `` |
| `intervention_id` | `uuid` | Yes | `` |
| `outcome` | `character varying` | Yes | `` |
| `outcome_date` | `timestamp with time zone` | Yes | `` |
| `outcome_notes` | `text` | Yes | `` |
| `consent_status` | `character varying` | No | `'not_asked'::character varying` |
| `consent_date` | `timestamp with time zone` | Yes | `` |
| `consent_method` | `character varying` | Yes | `` |
| `clinical_exclusions` | `jsonb` | Yes | `` |
| `switchback_detected` | `boolean` | No | `false` |
| `switchback_date` | `timestamp with time zone` | Yes | `` |
| `switchback_reason` | `text` | Yes | `` |
| `retention_expires_at` | `timestamp with time zone` | Yes | `` |
| `is_purged` | `boolean` | No | `false` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `practices`
**Row Count:** 7680

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `name` | `character varying` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `pcn_id` | `uuid` | Yes | `` |
| `icb_id` | `uuid` | No | `` |
| `clinical_system` | `character varying` | Yes | `` |
| `address` | `text` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `phone` | `character varying` | Yes | `` |
| `postcode` | `character varying` | Yes | `` |
| `website` | `character varying` | Yes | `` |
| `last_ods_sync` | `timestamp with time zone` | Yes | `` |
| `sub_icb_ods_code` | `character varying` | Yes | `` |
| `email_domain` | `character varying` | Yes | `` |

### Relationships
- `icb_id` → `icbs.id`
- `pcn_id` → `pcns.id`

### Sample Record
```json
{
  "name": "FREW TERRACE SURGERY",
  "ods_code": "S80698",
  "pcn_id": null,
  "icb_id": "95557472-5bee-41e8-af0d-e97885a581c0",
  "clinical_system": null,
  "address": "9 FREW TERRACE, IRVINE",
  "id": "889726ff-cb36-475d-af19-932308cab5a2",
  "created_at": "2026-03-07T17:28:22.398271+00:00",
  "updated_at": "2026-03-07T17:28:22.398271+00:00",
  "phone": null,
  "postcode": "KA12 9DY",
  "website": null,
  "last_ods_sync": null,
  "sub_icb_ods_code": null,
  "email_domain": "frewterrace.surgery.nhs.uk"
}
```

---

## Table: `prescribing_records`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `practice_ods_code` | `character varying` | No | `` |
| `bnf_code` | `character varying` | No | `` |
| `bnf_name` | `character varying` | No | `` |
| `items` | `integer` | No | `` |
| `quantity` | `double precision` | No | `` |
| `actual_cost` | `double precision` | No | `` |
| `nic` | `double precision` | No | `` |
| `period` | `character varying` | No | `` |
| `source` | `character varying` | No | `'openprescribing'::character varying` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

---

## Table: `price_snapshots`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `intervention_id` | `uuid` | Yes | `` |
| `stage` | `character varying` | No | `` |
| `current_drug_name` | `character varying` | No | `` |
| `alternative_drug_name` | `character varying` | No | `` |
| `current_bnf_code` | `character varying` | Yes | `` |
| `alternative_bnf_code` | `character varying` | Yes | `` |
| `current_unit_cost` | `double precision` | No | `` |
| `alternative_unit_cost` | `double precision` | No | `` |
| `items_per_month` | `integer` | No | `` |
| `current_monthly_cost` | `double precision` | No | `` |
| `alternative_monthly_cost` | `double precision` | No | `` |
| `gross_monthly_saving` | `double precision` | No | `` |
| `gross_annual_saving` | `double precision` | No | `` |
| `scenario_savings` | `jsonb` | Yes | `` |
| `data_source` | `character varying` | No | `` |
| `data_date` | `character varying` | Yes | `` |
| `drug_tariff_version` | `character varying` | Yes | `` |
| `price_concession_current` | `double precision` | No | `` |
| `price_concession_alternative` | `double precision` | No | `` |
| `rebate_per_unit` | `double precision` | No | `` |
| `baseline_monthly_spend` | `double precision` | Yes | `` |
| `post_implementation_spend` | `double precision` | Yes | `` |
| `switchback_cost` | `double precision` | No | `` |
| `months_measured` | `integer` | No | `` |
| `variance_from_discovery` | `double precision` | Yes | `` |
| `variance_from_forecast` | `double precision` | Yes | `` |
| `warnings` | `jsonb` | Yes | `` |
| `is_flagged` | `boolean` | No | `` |
| `flag_reason` | `text` | Yes | `` |
| `captured_by` | `character varying` | Yes | `` |
| `captured_at` | `timestamp with time zone` | No | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `intervention_id` → `interventions.id`
- `tenant_id` → `tenants.id`

---

## Table: `realized_savings`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `practice_ods_code` | `character varying` | No | `` |
| `pcn_ods_code` | `character varying` | Yes | `` |
| `workstream_id` | `uuid` | Yes | `` |
| `workstream_name` | `character varying` | Yes | `` |
| `period` | `character varying` | No | `` |
| `forecast_savings` | `double precision` | No | `` |
| `realized_savings` | `double precision` | No | `` |
| `variance` | `double precision` | No | `` |
| `patients_targeted` | `integer` | No | `` |
| `patients_switched` | `integer` | No | `` |
| `patients_switched_back` | `integer` | No | `` |
| `notes` | `text` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `realized_savings_monthly`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `intervention_id` | `uuid` | Yes | `` |
| `practice_ods_code` | `character varying` | No | `` |
| `pcn_ods_code` | `character varying` | Yes | `` |
| `workstream_name` | `character varying` | Yes | `` |
| `period` | `character varying` | No | `` |
| `baseline_spend` | `double precision` | No | `` |
| `post_switch_spend` | `double precision` | No | `` |
| `switchback_cost` | `double precision` | No | `` |
| `realized_saving` | `double precision` | No | `` |
| `forecast_saving` | `double precision` | No | `` |
| `variance` | `double precision` | No | `` |
| `variance_pct` | `double precision` | Yes | `` |
| `patients_on_target` | `integer` | No | `` |
| `patients_switched_back` | `integer` | No | `` |
| `is_underperforming` | `boolean` | No | `` |
| `flag_reason` | `text` | Yes | `` |
| `data_source` | `character varying` | No | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `intervention_id` → `interventions.id`
- `tenant_id` → `tenants.id`

---

## Table: `rebate_agreements`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `drug_name` | `character varying` | No | `` |
| `bnf_code` | `character varying` | Yes | `` |
| `rebate_type` | `character varying` | No | `` |
| `rebate_value` | `double precision` | No | `` |
| `volume_threshold` | `integer` | Yes | `` |
| `effective_from` | `date` | No | `` |
| `effective_to` | `date` | Yes | `` |
| `is_active` | `boolean` | No | `true` |
| `is_confidential` | `boolean` | No | `true` |
| `manufacturer` | `character varying` | Yes | `` |
| `notes` | `text` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

## Table: `sub_icb_display_names`
**Row Count:** 169

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `sub_icb_code` | `character varying` | No | `` |
| `display_name` | `text` | No | `` |
| `created_at` | `timestamp without time zone` | Yes | `now()` |
| `updated_at` | `timestamp without time zone` | Yes | `now()` |

### Sample Record
```json
{
  "id": "e18d3ff1-d5e5-4297-a509-5918c3fc28f9",
  "sub_icb_code": "00N",
  "display_name": "Nhs North East And North Cumbria Icb",
  "created_at": "2026-03-10T13:08:16.554409",
  "updated_at": "2026-03-10T13:08:24.304580"
}
```

---

## Table: `switching_opportunities`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `patient_id` | `uuid` | No | `` |
| `switching_rule_id` | `uuid` | No | `` |
| `status` | `character varying` | No | `'identified'::character varying` |
| `assigned_to_user_id` | `uuid` | Yes | `` |
| `estimated_annual_savings` | `numeric` | Yes | `` |
| `clinical_notes` | `text` | Yes | `` |
| `switch_date` | `date` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `is_deleted` | `boolean` | No | `false` |

### Relationships
- `assigned_to_user_id` → `users.id`
- `patient_id` → `patients.id`
- `switching_rule_id` → `switching_rules.id`

---

## Table: `switching_rules`
**Row Count:** 4

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `workstream` | `character varying` | No | `` |
| `from_medication_id` | `uuid` | No | `` |
| `to_medication_id` | `uuid` | Yes | `` |
| `risk_level` | `character varying` | No | `` |
| `inclusion_criteria` | `jsonb` | No | `'{}'::jsonb` |
| `exclusion_criteria` | `jsonb` | No | `'{}'::jsonb` |
| `estimated_savings_per_patient` | `numeric` | Yes | `` |
| `evidence_source` | `text` | Yes | `` |
| `is_active` | `boolean` | No | `true` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `from_medication_id` → `medications.id`
- `to_medication_id` → `medications.id`

### Sample Record
```json
{
  "workstream": "DPP-4 Inhibitor Switching",
  "from_medication_id": "06d51663-2194-4c80-a309-832ac0653129",
  "to_medication_id": "61a7090c-375c-49df-866d-5f287944ee03",
  "risk_level": "green",
  "inclusion_criteria": {
    "age": {
      "max": 85,
      "min": 18
    },
    "egfr_min": 30,
    "medication_type": "DPP-4 Inhibitor"
  },
  "exclusion_criteria": {
    "contraindications": [
      "Heart failure (NYHA III-IV)",
      "Hepatic impairment"
    ],
    "pancreatitis_history": true,
    "severe_renal_impairment": true
  },
  "estimated_savings_per_patient": "350.40",
  "evidence_source": "NICE NG28, RMOC DPP-4 guidance 2023",
  "is_active": true,
  "id": "9868393f-f138-4c2e-ac56-08fea7a1a742",
  "created_at": "2026-03-03T16:53:09.372048+00:00",
  "updated_at": null
}
```

---

## Table: `tenants`
**Row Count:** 2

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `name` | `character varying` | No | `` |
| `ods_code` | `character varying` | No | `` |
| `short_code` | `character varying` | No | `` |
| `status` | `character varying` | No | `'active'::character varying` |
| `branding` | `jsonb` | Yes | `` |
| `feature_flags` | `jsonb` | Yes | `'{}'::jsonb` |
| `data_retention_days` | `integer` | No | `2555` |
| `scoring_weights` | `jsonb` | Yes | `` |
| `primary_contact_name` | `character varying` | Yes | `` |
| `primary_contact_email` | `character varying` | Yes | `` |
| `onboarded_at` | `timestamp with time zone` | Yes | `` |
| `hierarchy_loaded` | `boolean` | No | `false` |
| `formulary_loaded` | `boolean` | No | `false` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `now()` |
| `is_deleted` | `boolean` | No | `false` |

### Sample Record
```json
{
  "id": "2dd0b5c9-95c2-4955-91cd-ec338b848957",
  "name": "Nhs Lancashire And South Cumbria Integrated Care Board",
  "ods_code": "QE1",
  "short_code": "QE1",
  "status": "active",
  "branding": null,
  "feature_flags": {},
  "data_retention_days": 2555,
  "scoring_weights": null,
  "primary_contact_name": null,
  "primary_contact_email": null,
  "onboarded_at": null,
  "hierarchy_loaded": false,
  "formulary_loaded": false,
  "created_at": "2026-03-04T16:49:53.873363+00:00",
  "updated_at": null,
  "is_deleted": false
}
```

---

## Table: `users`
**Row Count:** 24

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `email` | `character varying` | No | `` |
| `password_hash` | `character varying` | Yes | `` |
| `first_name` | `character varying` | No | `` |
| `last_name` | `character varying` | No | `` |
| `role` | `character varying` | No | `` |
| `icb_id` | `uuid` | No | `` |
| `is_active` | `boolean` | No | `true` |
| `last_login` | `timestamp with time zone` | Yes | `` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |
| `phone_number` | `character varying` | Yes | `` |
| `notification_preferences` | `jsonb` | Yes | `` |
| `practice_ods_code` | `character varying` | Yes | `` |
| `tenant_id` | `uuid` | Yes | `` |
| `pcn_ods_codes` | `jsonb` | Yes | `` |
| `invited_by_id` | `uuid` | Yes | `` |
| `invited_at` | `timestamp with time zone` | Yes | `` |
| `sub_icb_ods_code` | `character varying` | Yes | `` |
| `org_level` | `character varying` | Yes | `` |
| `org_ods_code` | `character varying` | Yes | `` |
| `org_name` | `character varying` | Yes | `` |

### Relationships
- `icb_id` → `icbs.id`
- `invited_by_id` → `users.id`
- `tenant_id` → `tenants.id`

### Sample Record
```json
{
  "email": "admin@qipp.nhs.uk",
  "password_hash": "$2b$12$LiJ1DJKI0IEug9uEdKZzDOtGmgpx2Ul93tRxogBFBwgl.1SG18Cge",
  "first_name": "System",
  "last_name": "Admin",
  "role": "admin",
  "icb_id": "e38d403b-7e3e-4d7e-96df-c6f4f3783c7b",
  "is_active": true,
  "last_login": "2026-03-04T18:04:03.482083+00:00",
  "id": "a6dd793a-8496-48ad-bc67-8c781512852b",
  "created_at": "2026-03-03T16:53:09.372048+00:00",
  "updated_at": "2026-03-04T18:04:01.453996+00:00",
  "phone_number": null,
  "notification_preferences": null,
  "practice_ods_code": null,
  "tenant_id": null,
  "pcn_ods_codes": null,
  "invited_by_id": null,
  "invited_at": null,
  "sub_icb_ods_code": null,
  "org_level": "icb",
  "org_ods_code": "QHL",
  "org_name": "Nhs Birmingham And Solihull Integrated Care Board"
}
```

---

## Table: `weekly_recommendations`
**Row Count:** 0

### Schema
| Column | Type | Nullable | Default |
|---|---|---|---|
| `tenant_id` | `uuid` | No | `` |
| `practice_ods_code` | `character varying` | Yes | `` |
| `pcn_ods_code` | `character varying` | Yes | `` |
| `week_commencing` | `date` | No | `` |
| `opportunity_id` | `character varying` | Yes | `` |
| `opportunity_title` | `character varying` | No | `` |
| `recommendation_type` | `character varying` | No | `` |
| `rationale` | `text` | Yes | `` |
| `estimated_savings` | `double precision` | Yes | `` |
| `priority_score` | `double precision` | Yes | `` |
| `alternative_opportunity_id` | `character varying` | Yes | `` |
| `alternative_rationale` | `text` | Yes | `` |
| `actioned` | `boolean` | No | `false` |
| `deferred` | `boolean` | No | `false` |
| `rejected` | `boolean` | No | `false` |
| `rejection_reason` | `text` | Yes | `` |
| `email_sent` | `boolean` | No | `false` |
| `notification_sent` | `boolean` | No | `false` |
| `id` | `uuid` | No | `` |
| `created_at` | `timestamp with time zone` | No | `now()` |
| `updated_at` | `timestamp with time zone` | Yes | `` |

### Relationships
- `tenant_id` → `tenants.id`

---

