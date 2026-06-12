from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import InviteStatus, SurveyStatus, ValidationStatus


class SurveyCreate(BaseModel):
    title: str
    city: str
    state: str = Field(min_length=2, max_length=2)
    external_form_provider: str = "limesurvey"
    external_form_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SurveyRead(SurveyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SurveyStatus
    created_at: datetime
    updated_at: datetime


class SurveyIntegrationUpdate(BaseModel):
    external_form_provider: str = "limesurvey"
    external_form_id: str


class InviteCreate(BaseModel):
    quantity: int = Field(ge=1, le=5000)
    source_channel: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    expires_in_hours: int | None = Field(default=None, gt=0)


class InviteTokenRead(BaseModel):
    id: int
    token: str
    external_token: str
    token_hash: str
    status: InviteStatus
    expires_at: datetime | None


class InviteBatchRead(BaseModel):
    survey_id: int
    invites: list[InviteTokenRead]


class InviteOpenValidate(BaseModel):
    token: str
    ip: str
    user_agent: str
    device_fingerprint: str


class InviteOpenResult(BaseModel):
    allowed: bool
    reason: str | None = None
    invite_id: int | None = None
    status: InviteStatus | None = None


class ResponseImport(BaseModel):
    survey_id: int
    token: str
    external_response_id: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    ip: str
    user_agent: str
    device_fingerprint: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ResponseValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    response_raw_id: int
    risk_score: int
    status: ValidationStatus
    flags: dict[str, Any]
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime


class ResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    survey_id: int
    invite_id: int
    external_response_id: str | None
    submitted_at: datetime
    duration_seconds: int | None
    source_channel: str | None
    raw_payload: dict[str, Any]
    validation: ResponseValidationRead | None


class ValidationUpdate(BaseModel):
    status: ValidationStatus
    review_notes: str | None = None
    reviewed_by: str


class ValidExportRow(BaseModel):
    response_id: int
    external_response_id: str | None
    submitted_at: datetime
    duration_seconds: int | None
    source_channel: str | None
    raw_payload: dict[str, Any]


ResponseStatusQuery = Literal["valid", "suspicious", "discarded"]
