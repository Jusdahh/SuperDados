from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


json_type = JSONB().with_variant(JSON(), "sqlite")


class SurveyStatus(StrEnum):
    draft = "draft"
    active = "active"
    closed = "closed"
    archived = "archived"


class InviteStatus(StrEnum):
    created = "created"
    opened = "opened"
    started = "started"
    completed = "completed"
    expired = "expired"
    blocked = "blocked"


class ValidationStatus(StrEnum):
    valid = "valid"
    suspicious = "suspicious"
    discarded = "discarded"


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SurveyStatus.draft.value, nullable=False)
    external_form_provider: Mapped[str] = mapped_column(String(50), default="limesurvey", nullable=False)
    external_form_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    invites: Mapped[list["SurveyInvite"]] = relationship(back_populates="survey")
    responses: Mapped[list["ResponseRaw"]] = relationship(back_populates="survey")


class SurveyInvite(Base):
    __tablename__ = "survey_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"), index=True, nullable=False)
    # Kept only to simplify LimeSurvey token import in the MVP; encrypt or omit in production.
    external_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=InviteStatus.created.value, index=True, nullable=False)
    source_channel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_device_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    survey: Mapped[Survey] = relationship(back_populates="invites")
    responses: Mapped[list["ResponseRaw"]] = relationship(back_populates="invite")


class ResponseRaw(Base):
    __tablename__ = "responses_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"), index=True, nullable=False)
    invite_id: Mapped[int] = mapped_column(ForeignKey("survey_invites.id"), index=True, nullable=False)
    external_response_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    device_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(json_type, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    survey: Mapped[Survey] = relationship(back_populates="responses")
    invite: Mapped[SurveyInvite] = relationship(back_populates="responses")
    validation: Mapped["ResponseValidation"] = relationship(back_populates="response_raw", uselist=False)


class ResponseValidation(Base):
    __tablename__ = "response_validations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    response_raw_id: Mapped[int] = mapped_column(ForeignKey("responses_raw.id"), unique=True, index=True, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    flags: Mapped[dict] = mapped_column(json_type, nullable=False, default=dict)
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    response_raw: Mapped[ResponseRaw] = relationship(back_populates="validation")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    before_json: Mapped[dict | None] = mapped_column(json_type, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(json_type, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
