from datetime import datetime, timedelta, timezone


def create_survey(client, city="Sao Paulo"):
    response = client.post(
        "/surveys",
        json={
            "title": "Pesquisa municipal",
            "city": city,
            "state": "SP",
            "external_form_provider": "limesurvey",
            "external_form_id": "LS-100",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_invite(client, survey_id, **overrides):
    payload = {
        "quantity": 1,
        "source_channel": "whatsapp",
        "utm_source": "panel",
        "utm_campaign": "mvp",
        "utm_content": "batch-a",
        "expires_in_hours": 24,
    }
    payload.update(overrides)
    response = client.post(f"/surveys/{survey_id}/invites", json=payload)
    assert response.status_code == 201
    return response.json()["invites"][0]


def open_invite(client, token, device="device-a"):
    return client.post(
        "/invites/validate-open",
        json={
            "token": token,
            "ip": "10.0.0.1",
            "user_agent": "pytest",
            "device_fingerprint": device,
        },
    )


def import_response(client, survey_id, token, **overrides):
    payload = {
        "survey_id": survey_id,
        "token": token,
        "external_response_id": "resp-1",
        "duration_seconds": 180,
        "ip": "10.0.0.1",
        "user_agent": "pytest",
        "device_fingerprint": "device-a",
        "raw_payload": {"municipio_votacao": "Sao Paulo", "attention_check": "correct", "voto": "A"},
    }
    payload.update(overrides)
    return client.post("/responses/import", json=payload)


def test_create_survey(client):
    survey = create_survey(client)
    assert survey["title"] == "Pesquisa municipal"
    assert survey["status"] == "draft"


def test_generate_invites(client):
    survey = create_survey(client)
    response = client.post(
        f"/surveys/{survey['id']}/invites",
        json={"quantity": 3, "source_channel": "email", "expires_in_hours": 24},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["invites"]) == 3
    assert data["invites"][0]["token"]


def test_validate_first_token_open(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])
    response = open_invite(client, invite["token"])
    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert response.json()["status"] == "opened"


def test_block_expired_token(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"], expires_in_hours=1)
    expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
    from app.core.security import hash_value
    from app.db.session import get_db
    from app.main import app
    from app.models import SurveyInvite

    db = next(app.dependency_overrides[get_db]())
    db.query(SurveyInvite).filter(SurveyInvite.token_hash == hash_value(invite["token"])).update({"expires_at": expired_at})
    db.commit()
    db.close()

    response = open_invite(client, invite["token"])
    assert response.json()["allowed"] is False
    assert response.json()["reason"] == "token_expired"


def test_block_completed_token(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])
    assert open_invite(client, invite["token"]).json()["allowed"] is True
    assert import_response(client, survey["id"], invite["token"]).status_code == 201
    second = import_response(client, survey["id"], invite["token"], external_response_id="resp-2")
    assert second.status_code == 409
    assert second.json()["detail"] == "token_completed"


def test_block_open_on_different_device(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])
    assert open_invite(client, invite["token"], device="device-a").json()["allowed"] is True
    response = open_invite(client, invite["token"], device="device-b")
    assert response.json()["allowed"] is False
    assert response.json()["reason"] == "device_mismatch"
    assert response.json()["status"] == "blocked"


def test_import_valid_response(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])
    assert open_invite(client, invite["token"]).json()["allowed"] is True
    response = import_response(client, survey["id"], invite["token"])
    assert response.status_code == 201
    data = response.json()
    assert data["validation"]["status"] == "valid"
    assert data["validation"]["risk_score"] == 0


def test_mark_suspicious_for_short_duration(client):
    survey = create_survey(client)
    invite = create_invite(client, survey["id"])
    assert open_invite(client, invite["token"]).json()["allowed"] is True
    response = import_response(client, survey["id"], invite["token"], duration_seconds=30)
    assert response.status_code == 201
    validation = response.json()["validation"]
    assert validation["status"] == "suspicious"
    assert "very_short_duration" in validation["flags"]


def test_mark_discarded_for_different_city(client):
    survey = create_survey(client, city="Sao Paulo")
    invite = create_invite(client, survey["id"])
    assert open_invite(client, invite["token"]).json()["allowed"] is True
    response = import_response(
        client,
        survey["id"],
        invite["token"],
        raw_payload={"municipio_votacao": "Campinas", "attention_check": "correct"},
    )
    assert response.status_code == 201
    validation = response.json()["validation"]
    assert validation["status"] == "discarded"
    assert "outside_target_city" in validation["flags"]


def test_export_only_valid_responses(client):
    survey = create_survey(client)
    valid_invite = create_invite(client, survey["id"])
    discarded_invite = create_invite(client, survey["id"])
    assert open_invite(client, valid_invite["token"], device="device-a").json()["allowed"] is True
    assert open_invite(client, discarded_invite["token"], device="device-b").json()["allowed"] is True

    assert import_response(client, survey["id"], valid_invite["token"], device_fingerprint="device-a").status_code == 201
    assert (
        import_response(
            client,
            survey["id"],
            discarded_invite["token"],
            external_response_id="resp-2",
            device_fingerprint="device-b",
            raw_payload={"municipio_votacao": "Campinas", "attention_check": "correct"},
        ).status_code
        == 201
    )

    export = client.get(f"/surveys/{survey['id']}/exports/valid-responses")
    assert export.status_code == 200
    rows = export.json()
    assert len(rows) == 1
    assert rows[0]["external_response_id"] == "resp-1"
