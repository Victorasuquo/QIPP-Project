import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ActionSheet(Base):
    __tablename__ = "action_sheets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workstream: Mapped[str] = mapped_column(String, nullable=False)
    icb_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("icbs.id"), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    practice_ods_code: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    template_version: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="draft")
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    therapeutic_area: Mapped[str | None] = mapped_column(String, nullable=True)
    workstream_code: Mapped[str | None] = mapped_column(String, nullable=True)
    current_drug: Mapped[str] = mapped_column(String, nullable=False)
    target_drug: Mapped[str] = mapped_column(String, nullable=False)
    preferred_product: Mapped[str | None] = mapped_column(String, nullable=True)
    current_drug_bnf: Mapped[str | None] = mapped_column(String, nullable=True)
    target_drug_bnf: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_changed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    forecast_annual_savings: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_savings: Mapped[float] = mapped_column(Float, default=0.0)
    switchback_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_eligible_patients: Mapped[int] = mapped_column(Integer, default=0)
    patients_switched: Mapped[int] = mapped_column(Integer, default=0)
    patients_refused: Mapped[int] = mapped_column(Integer, default=0)
    patients_excluded: Mapped[int] = mapped_column(Integer, default=0)
    patients_switched_back: Mapped[int] = mapped_column(Integer, default=0)
    clinical_rule_set: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    practice_ods_codes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    state_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RealizedSaving(Base):
    __tablename__ = "realized_savings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    practice_ods_code: Mapped[str | None] = mapped_column(String, nullable=True)
    period: Mapped[str] = mapped_column(String, nullable=False)
    actual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    workstream: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RealizedSavingMonthly(Base):
    __tablename__ = "realized_savings_monthly"  # V1 name — note the 's'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    intervention_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    practice_ods_code: Mapped[str] = mapped_column(String, nullable=False)
    pcn_ods_code: Mapped[str | None] = mapped_column(String, nullable=True)
    workstream_name: Mapped[str | None] = mapped_column(String, nullable=True)  # V1 col name
    period: Mapped[str] = mapped_column(String, nullable=False)
    baseline_spend: Mapped[float] = mapped_column(Float, default=0.0)
    post_switch_spend: Mapped[float] = mapped_column(Float, default=0.0)
    switchback_cost: Mapped[float] = mapped_column(Float, default=0.0)
    realized_saving: Mapped[float] = mapped_column(Float, default=0.0)  # V1 col name
    forecast_saving: Mapped[float] = mapped_column(Float, default=0.0)
    variance: Mapped[float] = mapped_column(Float, default=0.0)
    variance_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    patients_on_target: Mapped[int] = mapped_column(Integer, default=0)
    patients_switched_back: Mapped[int] = mapped_column(Integer, default=0)
    is_underperforming: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
