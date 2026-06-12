from urllib.parse import parse_qs, urlparse
from datetime import timedelta

from app.core.security import hash_value
from app.db.session import get_db
from app.main import app
from app.models import InviteStatus, SurveyInvite, utc_now

from tests.test_flow import create_invite, create_survey


def test_public_entry_assigns_pool_token_and_redirects(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])

    response = client.get(
        f"/entry/{survey['id']}?utm_source=meta&utm_campaign=teste",
        follow_redirects=False,
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["location"])
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://survey.example/LS-100"
    assert parse_qs(parsed.query)["token"] == [invite["token"]]
    assert parse_qs(parsed.query)["lang"] == ["pt"]
    assert "sd_browser_id=" in response.headers["set-cookie"]

    db = next(app.dependency_overrides[get_db]())
    stored = db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(invite["token"])).one()
    assert stored.status == InviteStatus.opened.value
    assert stored.first_device_hash
    assert stored.utm_source == "meta"
    assert stored.utm_campaign == "teste"
    db.close()


def test_update_survey_integration(client):
    survey = create_survey(client)

    response = client.patch(
        f"/surveys/{survey['id']}/integration",
        json={"external_form_provider": "limesurvey", "external_form_id": "318945"},
    )

    assert response.status_code == 200
    assert response.json()["external_form_id"] == "318945"


def test_public_entry_reuses_same_token_for_same_browser(client):
    survey = create_survey(client)
    first_invite = create_invite(client, survey["id"])
    second_invite = create_invite(client, survey["id"])

    first_response = client.get(f"/entry/{survey['id']}", follow_redirects=False)
    second_response = client.get(f"/entry/{survey['id']}", follow_redirects=False)

    first_token = parse_qs(urlparse(first_response.headers["location"]).query)["token"][0]
    second_token = parse_qs(urlparse(second_response.headers["location"]).query)["token"][0]
    assert first_token == first_invite["token"]
    assert second_token == first_invite["token"]

    db = next(app.dependency_overrides[get_db]())
    untouched = db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(second_invite["token"])).one()
    assert untouched.status == InviteStatus.created.value
    assert untouched.first_device_hash is None
    db.close()


def test_public_entry_skips_old_limesurvey_incompatible_tokens(client):
    survey = create_survey(client)
    old_invalid_invite = create_invite(client, survey["id"])
    valid_invite = create_invite(client, survey["id"])

    db = next(app.dependency_overrides[get_db]())
    stored_invalid = db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(old_invalid_invite["token"])).one()
    stored_invalid.external_token = "token-com-hifen-e-muito-muito-muito-longo"
    db.commit()
    db.close()

    response = client.get(f"/entry/{survey['id']}", follow_redirects=False)

    assert response.status_code == 302
    token = parse_qs(urlparse(response.headers["location"]).query)["token"][0]
    assert token == valid_invite["token"]

    db = next(app.dependency_overrides[get_db]())
    blocked = db.query(SurveyInvite).filter(SurveyInvite.id == old_invalid_invite["id"]).one()
    assert blocked.status == InviteStatus.blocked.value
    db.close()


def test_public_entry_skips_expired_pool_tokens(client):
    survey = create_survey(client)
    expired_invite = create_invite(client, survey["id"])
    valid_invite = create_invite(client, survey["id"])

    db = next(app.dependency_overrides[get_db]())
    stored_expired = db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(expired_invite["token"])).one()
    stored_expired.expires_at = utc_now() - timedelta(hours=1)
    db.commit()
    db.close()

    response = client.get(f"/entry/{survey['id']}", follow_redirects=False)

    assert response.status_code == 302
    token = parse_qs(urlparse(response.headers["location"]).query)["token"][0]
    assert token == valid_invite["token"]

    db = next(app.dependency_overrides[get_db]())
    skipped = db.query(SurveyInvite).filter(SurveyInvite.id == expired_invite["id"]).one()
    assert skipped.status == InviteStatus.expired.value
    db.close()


def test_public_entry_force_new_ignores_existing_browser_cookie(client):
    survey = create_survey(client)
    first_invite = create_invite(client, survey["id"])
    second_invite = create_invite(client, survey["id"])

    first_response = client.get(f"/entry/{survey['id']}", follow_redirects=False)
    forced_response = client.get(f"/entry/{survey['id']}?force_new=true", follow_redirects=False)

    first_token = parse_qs(urlparse(first_response.headers["location"]).query)["token"][0]
    forced_token = parse_qs(urlparse(forced_response.headers["location"]).query)["token"][0]
    assert first_token == first_invite["token"]
    assert forced_token == second_invite["token"]


def test_public_entry_returns_error_when_pool_is_empty(client):
    survey = create_survey(client)

    response = client.get(f"/entry/{survey['id']}", follow_redirects=False)

    assert response.status_code == 503
    assert response.json()["detail"] == "invite_pool_empty"
