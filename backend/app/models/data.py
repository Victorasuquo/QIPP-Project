import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Text, Integer, Float, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    total_records: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataFreshness(Base):
    __tablename__ = "data_freshness"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_expected: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PatentExpiry(Base):
    __tablename__ = "patent_expiries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bnf_code: Mapped[str] = mapped_column(String, nullable=False)
    drug_name: Mapped[str] = mapped_column(String, nullable=False)
    brand_name: Mapped[str] = mapped_column(String, nullable=False)
    patent_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    generic_available_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    branded_unit_price_pence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generic_unit_price_pence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_price_drop_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    estimated_annual_saving_gbp: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    monitoring_status: Mapped[str] = mapped_column(String, default="upcoming")
    source: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_auto_created: Mapped[bool] = mapped_column(Boolean, default=False)
    on_watch_list: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PIIPatientRecord(Base):
    __tablename__ = "pii_patient_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nhs_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    nhs_number_hash: Mapped[str] = mapped_column(String, nullable=False)
    name_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_of_birth_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    practice_ods_code: Mapped[str] = mapped_column(String, nullable=False)
    age_band: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    current_medications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    intervention_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("interventions.id"), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    outcome_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_status: Mapped[str] = mapped_column(String, default="not_asked")
    consent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_method: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PIIAccessLog(Base):
    __tablename__ = "pii_access_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    accessor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accessor_role: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    patient_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pii_patient_records.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    access_reason: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EpactRecord(Base):
    __tablename__ = "epact_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    practice_ods_code: Mapped[str] = mapped_column(String, nullable=False)
    bnf_code: Mapped[str] = mapped_column(String, nullable=False)
    bnf_name: Mapped[str] = mapped_column(String, nullable=False)
    items: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=False)
    nic: Mapped[float] = mapped_column(Float, nullable=False)
    formulation: Mapped[str | None] = mapped_column(String, nullable=True)
    strength: Mapped[str | None] = mapped_column(String, nullable=True)
    period: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PatientWorklistItem(Base):
    __tablename__ = "patient_worklist_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    intervention_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interventions.id"), nullable=False)
    practice_ods_code: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    nhs_number: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_name: Mapped[str] = mapped_column(String, nullable=False)
    current_drug: Mapped[str] = mapped_column(String, nullable=False)
    current_dose: Mapped[str | None] = mapped_column(String, nullable=True)
    target_drug: Mapped[str] = mapped_column(String, nullable=False)
    preferred_product: Mapped[str | None] = mapped_column(String, nullable=True)
    is_care_home: Mapped[bool] = mapped_column(Boolean, default=False)
    has_renal_impairment: Mapped[bool] = mapped_column(Boolean, default=False)
    has_prior_switchback: Mapped[bool] = mapped_column(Boolean, default=False)
    has_specialist_instruction: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_flags_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    letter_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    switchback_count: Mapped[int] = mapped_column(Integer, default=0)
    actioned_by: Mapped[str | None] = mapped_column(String, nullable=True)
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DrugTariffPrice(Base):
    __tablename__ = "drug_tariff_prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_name: Mapped[str] = mapped_column(String, nullable=False)
    bnf_code: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    price_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    is_concession: Mapped[bool] = mapped_column(Boolean, default=False)
    pack_size: Mapped[str | None] = mapped_column(String, nullable=True)
    formulation: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DMDProduct(Base):
    __tablename__ = "dmd_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dmd_code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bnf_code: Mapped[str | None] = mapped_column(String, nullable=True)
    product_type: Mapped[str] = mapped_column(String, nullable=False)
    vmp_code: Mapped[str | None] = mapped_column(String, nullable=True)
    form: Mapped[str | None] = mapped_column(String, nullable=True)
    route: Mapped[str | None] = mapped_column(String, nullable=True)
    strength: Mapped[str | None] = mapped_column(String, nullable=True)
    supplier: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
