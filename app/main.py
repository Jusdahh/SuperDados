from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import hash_value
from app.db.base import Base
from app.db.session import engine, get_db
from app.models import (
    InviteStatus,
    ResponseRaw,
    ResponseValidation,
    Survey,
    SurveyInvite,
    ValidationStatus,
    utc_now,
)
from app.schemas import (
    InviteBatchRead,
    InviteCreate,
    InviteOpenResult,
    InviteOpenValidate,
    InviteTokenRead,
    ResponseImport,
    ResponseRead,
    ResponseStatusQuery,
    SurveyCreate,
    SurveyIntegrationUpdate,
    SurveyRead,
    ValidationUpdate,
    ValidExportRow,
)
from app.services.audit import log_audit
from app.services.invites import generate_invite_token, is_expired, is_limesurvey_token_compatible, validate_open
from app.services.risk_scoring import calculate_risk_score

app = FastAPI(title="SuperDados Anticontaminacao API", version="0.1.0")


@app.on_event("startup")
def create_sqlite_tables_for_local_dev() -> None:
    settings = get_settings()
    if settings.app_env == "local" and settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "SuperDados Anticontaminacao API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


def _request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@app.get("/entry/{survey_id}", include_in_schema=True)
def public_survey_entry(
    survey_id: int,
    request: Request,
    source_channel: str = Query(default="meta_ads"),
    utm_source: str | None = Query(default=None),
    utm_campaign: str | None = Query(default=None),
    utm_content: str | None = Query(default=None),
    lang: str = Query(default="pt"),
    force_new: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    survey = db.get(Survey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="survey_not_found")
    if not survey.external_form_id:
        raise HTTPException(status_code=400, detail="survey_external_form_id_missing")

    settings = get_settings()
    if not settings.limesurvey_base_url:
        raise HTTPException(status_code=503, detail="limesurvey_base_url_not_configured")

    browser_key = None if force_new else request.cookies.get("sd_browser_id")
    browser_key = browser_key or token_urlsafe(32)
    browser_hash = hash_value(browser_key)
    invite = None
    if not force_new:
        invite = (
            db.query(SurveyInvite)
            .filter(
                SurveyInvite.survey_id == survey.id,
                SurveyInvite.first_device_hash == browser_hash,
            )
            .order_by(SurveyInvite.created_at.desc())
            .first()
        )
        if invite and (is_expired(invite) or not is_limesurvey_token_compatible(invite.external_token)):
            invite.status = InviteStatus.expired.value if is_expired(invite) else InviteStatus.blocked.value
            log_audit(
                db,
                entity_type="survey_invite",
                entity_id=invite.id,
                action="public_entry_existing_invite_skipped",
                after_json={"reason": "expired_or_invalid_for_limesurvey"},
            )
            db.flush()
            invite = None

    if invite is None:
        candidates = (
            db.query(SurveyInvite)
            .filter(
                SurveyInvite.survey_id == survey.id,
                SurveyInvite.status == InviteStatus.created.value,
                SurveyInvite.first_device_hash.is_(None),
            )
            .order_by(SurveyInvite.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(100)
            .all()
        )
        invite = None
        for candidate in candidates:
            if is_expired(candidate):
                candidate.status = InviteStatus.expired.value
                log_audit(
                    db,
                    entity_type="survey_invite",
                    entity_id=candidate.id,
                    action="expired_invite_skipped",
                    after_json={"reason": "expired_before_public_entry"},
                )
                continue
            if is_limesurvey_token_compatible(candidate.external_token):
                invite = candidate
                break
            candidate.status = InviteStatus.blocked.value
            log_audit(
                db,
                entity_type="survey_invite",
                entity_id=candidate.id,
                action="invalid_limesurvey_token_blocked",
                after_json={"reason": "incompatible_token_format"},
            )
        if invite is None:
            db.commit()
            raise HTTPException(status_code=503, detail="invite_pool_empty")

        invite.status = InviteStatus.opened.value
        invite.source_channel = source_channel
        invite.utm_source = utm_source
        invite.utm_campaign = utm_campaign
        invite.utm_content = utm_content
        invite.first_ip_hash = hash_value(_request_ip(request))
        invite.first_device_hash = browser_hash
        invite.first_user_agent_hash = hash_value(request.headers.get("user-agent", ""))
        invite.first_opened_at = utc_now()
        db.flush()
        log_audit(
            db,
            entity_type="survey_invite",
            entity_id=invite.id,
            action="public_entry_assigned",
            after_json={
                "survey_id": survey.id,
                "source_channel": source_channel,
                "utm_source": utm_source,
                "utm_campaign": utm_campaign,
            },
        )
        db.commit()

    query = urlencode({"lang": lang, "token": invite.external_token})
    redirect = RedirectResponse(
        url=f"{settings.limesurvey_base_url}/{survey.external_form_id}?{query}",
        status_code=302,
    )
    redirect.set_cookie(
        key="sd_browser_id",
        value=browser_key,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=settings.public_cookie_secure,
        samesite="lax",
    )
    return redirect


@app.post("/surveys", response_model=SurveyRead, status_code=201)
def create_survey(payload: SurveyCreate, db: Session = Depends(get_db)) -> Survey:
    survey = Survey(**payload.model_dump())
    db.add(survey)
    db.flush()
    log_audit(
        db,
        entity_type="survey",
        entity_id=survey.id,
        action="created",
        after_json={"title": survey.title, "city": survey.city, "state": survey.state},
    )
    db.commit()
    db.refresh(survey)
    return survey


@app.get("/surveys", response_model=list[SurveyRead])
def list_surveys(db: Session = Depends(get_db)) -> list[Survey]:
    return db.query(Survey).order_by(Survey.created_at.desc()).all()


@app.patch("/surveys/{survey_id}/integration", response_model=SurveyRead)
def update_survey_integration(
    survey_id: int,
    payload: SurveyIntegrationUpdate,
    db: Session = Depends(get_db),
) -> Survey:
    survey = db.get(Survey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="survey_not_found")

    before = {
        "external_form_provider": survey.external_form_provider,
        "external_form_id": survey.external_form_id,
    }
    survey.external_form_provider = payload.external_form_provider
    survey.external_form_id = payload.external_form_id
    log_audit(
        db,
        entity_type="survey",
        entity_id=survey.id,
        action="integration_updated",
        before_json=before,
        after_json=payload.model_dump(),
    )
    db.commit()
    db.refresh(survey)
    return survey


@app.post("/surveys/{survey_id}/invites", response_model=InviteBatchRead, status_code=201)
def create_invites(survey_id: int, payload: InviteCreate, db: Session = Depends(get_db)) -> InviteBatchRead:
    survey = db.get(Survey, survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="survey_not_found")

    expires_at = utc_now() + timedelta(hours=payload.expires_in_hours) if payload.expires_in_hours else None
    results: list[InviteTokenRead] = []

    for _ in range(payload.quantity):
        token = generate_invite_token()
        invite = SurveyInvite(
            survey_id=survey.id,
            external_token=token,
            token_hash=hash_value(token),
            source_channel=payload.source_channel,
            utm_source=payload.utm_source,
            utm_campaign=payload.utm_campaign,
            utm_content=payload.utm_content,
            expires_at=expires_at,
        )
        db.add(invite)
        db.flush()
        results.append(
            InviteTokenRead(
                id=invite.id,
                token=token,
                external_token=token,
                token_hash=invite.token_hash,
                status=InviteStatus(invite.status),
                expires_at=invite.expires_at,
            )
        )

    log_audit(
        db,
        entity_type="survey",
        entity_id=survey.id,
        action="invites_created",
        after_json={"quantity": payload.quantity, "source_channel": payload.source_channel},
    )
    db.commit()
    return InviteBatchRead(survey_id=survey.id, invites=results)


@app.post("/invites/validate-open", response_model=InviteOpenResult)
def validate_invite_open(payload: InviteOpenValidate, db: Session = Depends(get_db)) -> InviteOpenResult:
    allowed, reason, invite = validate_open(
        db,
        token=payload.token,
        ip=payload.ip,
        user_agent=payload.user_agent,
        device_fingerprint=payload.device_fingerprint,
    )
    if invite is not None and reason:
        log_audit(
            db,
            entity_type="survey_invite",
            entity_id=invite.id,
            action="open_blocked",
            after_json={"reason": reason, "status": invite.status},
        )
    db.commit()
    return InviteOpenResult(
        allowed=allowed,
        reason=reason,
        invite_id=invite.id if invite else None,
        status=InviteStatus(invite.status) if invite else None,
    )


def _load_import_invite(db: Session, payload: ResponseImport) -> SurveyInvite:
    invite = (
        db.query(SurveyInvite)
        .filter(SurveyInvite.survey_id == payload.survey_id, SurveyInvite.token_hash == hash_value(payload.token))
        .first()
    )
    if invite is None:
        raise HTTPException(status_code=403, detail="token_not_found")
    if is_expired(invite):
        invite.status = InviteStatus.expired.value
        db.commit()
        raise HTTPException(status_code=403, detail="token_expired")
    if invite.status == InviteStatus.completed.value:
        raise HTTPException(status_code=409, detail="token_completed")
    if invite.status == InviteStatus.blocked.value:
        raise HTTPException(status_code=403, detail="token_blocked")
    return invite


@app.post("/responses/import", response_model=ResponseRead, status_code=201)
def import_response(payload: ResponseImport, db: Session = Depends(get_db)) -> ResponseRaw:
    survey = db.get(Survey, payload.survey_id)
    if survey is None:
        raise HTTPException(status_code=404, detail="survey_not_found")

    invite = _load_import_invite(db, payload)
    device_hash = hash_value(payload.device_fingerprint) if payload.device_fingerprint else None
    if invite.first_device_hash and invite.first_device_hash != device_hash:
        if device_hash is not None:
            invite.status = InviteStatus.blocked.value
            db.commit()
            raise HTTPException(status_code=403, detail="device_mismatch")

    response = ResponseRaw(
        survey_id=survey.id,
        invite_id=invite.id,
        external_response_id=payload.external_response_id,
        duration_seconds=payload.duration_seconds,
        ip_hash=hash_value(payload.ip),
        device_hash=device_hash,
        user_agent_hash=hash_value(payload.user_agent),
        source_channel=invite.source_channel,
        raw_payload=payload.raw_payload,
    )
    db.add(response)
    db.flush()

    invite.status = InviteStatus.completed.value
    invite.completed_at = utc_now()

    scoring = calculate_risk_score(response, invite, db)
    db.add(
        ResponseValidation(
            response_raw_id=response.id,
            risk_score=scoring["risk_score"],
            flags=scoring["flags"],
            status=scoring["status"],
        )
    )
    log_audit(
        db,
        entity_type="response_raw",
        entity_id=response.id,
        action="imported",
        after_json={"validation_status": scoring["status"], "risk_score": scoring["risk_score"]},
    )
    db.commit()
    return (
        db.query(ResponseRaw)
        .options(joinedload(ResponseRaw.validation))
        .filter(ResponseRaw.id == response.id)
        .one()
    )


@app.get("/surveys/{survey_id}/responses", response_model=list[ResponseRead])
def list_responses(
    survey_id: int,
    status: ResponseStatusQuery | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ResponseRaw]:
    query = (
        db.query(ResponseRaw)
        .options(joinedload(ResponseRaw.validation))
        .filter(ResponseRaw.survey_id == survey_id)
        .join(ResponseValidation)
    )
    if status:
        query = query.filter(ResponseValidation.status == status)
    return query.order_by(ResponseRaw.created_at.desc()).all()


@app.patch("/responses/{response_id}/validation", response_model=ResponseRead)
def review_response_validation(
    response_id: int,
    payload: ValidationUpdate,
    db: Session = Depends(get_db),
) -> ResponseRaw:
    response = (
        db.query(ResponseRaw)
        .options(joinedload(ResponseRaw.validation))
        .filter(ResponseRaw.id == response_id)
        .first()
    )
    if response is None or response.validation is None:
        raise HTTPException(status_code=404, detail="response_validation_not_found")

    before = {"status": response.validation.status, "review_notes": response.validation.review_notes}
    response.validation.status = payload.status.value
    response.validation.review_notes = payload.review_notes
    response.validation.reviewed_by = payload.reviewed_by
    response.validation.reviewed_at = utc_now()
    log_audit(
        db,
        entity_type="response_validation",
        entity_id=response.validation.id,
        action="reviewed",
        before_json=before,
        after_json={"status": response.validation.status, "reviewed_by": payload.reviewed_by},
    )
    db.commit()
    db.refresh(response)
    return response


@app.get("/surveys/{survey_id}/exports/valid-responses", response_model=list[ValidExportRow])
def export_valid_responses(survey_id: int, db: Session = Depends(get_db)) -> list[ValidExportRow]:
    responses = (
        db.query(ResponseRaw)
        .join(ResponseValidation)
        .filter(ResponseRaw.survey_id == survey_id, ResponseValidation.status == ValidationStatus.valid.value)
        .order_by(ResponseRaw.submitted_at.asc())
        .all()
    )
    return [
        ValidExportRow(
            response_id=response.id,
            external_response_id=response.external_response_id,
            submitted_at=response.submitted_at,
            duration_seconds=response.duration_seconds,
            source_channel=response.source_channel,
            raw_payload=response.raw_payload,
        )
        for response in responses
    ]
