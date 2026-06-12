from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import ResponseRaw, SurveyInvite, ValidationStatus, utc_now

VALID_MAX_SCORE = 29
SUSPICIOUS_MAX_SCORE = 69

VERY_SHORT_DURATION_SECONDS = 60
MANY_RESPONSES_SAME_IP_LIMIT = 5
MANY_RESPONSES_WINDOW_HOURS = 1
SAME_DEVICE_RESPONSE_LIMIT = 1

SCORE_VERY_SHORT_DURATION = 30
SCORE_OUTSIDE_TARGET_CITY = 80
SCORE_FAILED_ATTENTION_CHECK = 50
SCORE_MANY_RESPONSES_SAME_IP = 30
SCORE_SAME_DEVICE_MULTIPLE_RESPONSES = 80
SCORE_TOKEN_DEVICE_MISMATCH = 70
SCORE_MISSING_SOURCE_CHANNEL = 20


def _attention_check_failed(raw_payload: dict[str, Any]) -> bool:
    value = raw_payload.get("attention_check")
    if value is None:
        return False
    if isinstance(value, bool):
        return not value
    return str(value).strip().lower() not in {"ok", "correct", "correto", "true", "1", "sim"}


def _classify(score: int) -> str:
    if score <= VALID_MAX_SCORE:
        return ValidationStatus.valid.value
    if score <= SUSPICIOUS_MAX_SCORE:
        return ValidationStatus.suspicious.value
    return ValidationStatus.discarded.value


def calculate_risk_score(response: ResponseRaw, invite: SurveyInvite, db: Session) -> dict[str, Any]:
    score = 0
    flags: dict[str, Any] = {}
    raw_payload = response.raw_payload or {}

    if response.duration_seconds is not None and response.duration_seconds < VERY_SHORT_DURATION_SECONDS:
        score += SCORE_VERY_SHORT_DURATION
        flags["very_short_duration"] = True

    municipio = raw_payload.get("municipio_votacao")
    if municipio and response.survey and municipio.strip().lower() != response.survey.city.strip().lower():
        score += SCORE_OUTSIDE_TARGET_CITY
        flags["outside_target_city"] = True

    if _attention_check_failed(raw_payload):
        score += SCORE_FAILED_ATTENTION_CHECK
        flags["failed_attention_check"] = True

    if response.ip_hash:
        window_start = utc_now() - timedelta(hours=MANY_RESPONSES_WINDOW_HOURS)
        same_ip_count = (
            db.query(ResponseRaw)
            .filter(ResponseRaw.ip_hash == response.ip_hash, ResponseRaw.created_at >= window_start)
            .count()
        )
        if same_ip_count > MANY_RESPONSES_SAME_IP_LIMIT:
            score += SCORE_MANY_RESPONSES_SAME_IP
            flags["many_responses_same_ip"] = {"count": same_ip_count}

    if response.device_hash:
        same_device_count = db.query(ResponseRaw).filter(ResponseRaw.device_hash == response.device_hash).count()
        if same_device_count > SAME_DEVICE_RESPONSE_LIMIT:
            score += SCORE_SAME_DEVICE_MULTIPLE_RESPONSES
            flags["same_device_multiple_responses"] = {"count": same_device_count}

    if invite.first_device_hash and response.device_hash and invite.first_device_hash != response.device_hash:
        score += SCORE_TOKEN_DEVICE_MISMATCH
        flags["token_device_mismatch"] = True

    if not response.source_channel:
        score += SCORE_MISSING_SOURCE_CHANNEL
        flags["missing_source_channel"] = True

    return {"risk_score": score, "flags": flags, "status": _classify(score)}
