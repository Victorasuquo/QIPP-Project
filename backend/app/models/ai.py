import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class AIRuleSet(Base):
    __tablename__ = "ai_rule_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_set_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transpiled_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_system: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_rule_sets.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    therapeutic_area: Mapped[str | None] = mapped_column(String, nullable=True)
    estimated_patient_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_file_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    safety_warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    requires_manual_review_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    guardrail_safe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    flagged_phrases: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AIDecisionAudit(Base):
    __tablename__ = "ai_decision_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rule_set_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_rule_sets.id"), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    guardrail_safe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    flagged_phrases: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    human_action: Mapped[str | None] = mapped_column(String, nullable=True)
    human_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class WeeklyRecommendation(Base):
    __tablename__ = "weekly_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    workstream: Mapped[str | None] = mapped_column(String, nullable=True)
    recommendation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(String, nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
