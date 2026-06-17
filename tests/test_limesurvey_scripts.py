import argparse
import csv
import re

from app.services.invites import generate_invite_token, is_limesurvey_token_compatible
from scripts import limesurvey_export_invites, limesurvey_import_responses


def test_export_invites_writes_limesurvey_csv(tmp_path, monkeypatch):
    output = tmp_path / "participants.csv"

    def fake_post_json(base_url, path, payload, timeout=30):
        assert base_url == "http://testserver"
        assert path == "/surveys/10/invites"
        assert payload["quantity"] == 2
        return {
            "survey_id": 10,
            "invites": [
                {"id": 1, "token": "token_a", "expires_at": "2026-06-04T12:00:00+00:00"},
                {"id": 2, "token": "token_b", "expires_at": None},
            ],
        }

    monkeypatch.setattr(limesurvey_export_invites, "post_json", fake_post_json)
    args = argparse.Namespace(
        base_url="http://testserver",
        survey_id=10,
        quantity=2,
        output=str(output),
        source_channel="whatsapp",
        utm_source="panel",
        utm_campaign="mvp",
        utm_content="batch-a",
        expires_in_hours=24,
        language="",
        email_domain="invalid.example",
        timeout=30,
    )

    rows = limesurvey_export_invites.export_invites(args)

    assert len(rows) == 2
    with output.open(encoding="utf-8-sig", newline="") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))

    assert csv_rows[0]["firstname"] == "Respondente 1"
    assert csv_rows[0]["email"] == "token_a@invalid.example"
    assert csv_rows[0]["token"] == "token_a"
    assert csv_rows[0]["usesleft"] == "1"
    assert csv_rows[0]["language"] == ""
    assert csv_rows[0]["validuntil"] == "2026-06-04 12:00:00"
    assert csv_rows[0]["attribute_1"] == "1"
    assert csv_rows[0]["attribute_2"] == "whatsapp"


def test_generated_invite_token_is_limesurvey_compatible():
    token = generate_invite_token()
    assert len(token) <= 36
    assert re.fullmatch(r"[0-9A-Za-z_]+", token)
    assert is_limesurvey_token_compatible(token)


def test_import_responses_posts_rows_to_backend(tmp_path, monkeypatch):
    input_path = tmp_path / "responses.csv"
    input_path.write_text(
        "id,token,startdate,submitdate,ipaddr,user_agent,device_fingerprint,municipio_votacao,attention_check\n"
        "100,token-a,2026-06-03 10:00:00,2026-06-03 10:03:00,10.0.0.1,ua,dev-a,Sao Paulo,correct\n",
        encoding="utf-8",
    )
    posted_payloads = []

    def fake_post_json(base_url, path, payload, timeout=30):
        posted_payloads.append(payload)
        return {"id": 1}

    monkeypatch.setattr(limesurvey_import_responses, "post_json", fake_post_json)
    args = limesurvey_import_responses.build_parser().parse_args(
        [
            "--base-url",
            "http://testserver",
            "--survey-id",
            "10",
            "--input",
            str(input_path),
        ]
    )

    stats = limesurvey_import_responses.import_responses(args)

    assert stats == {"imported": 1, "failed": 0}
    payload = posted_payloads[0]
    assert payload["survey_id"] == 10
    assert payload["token"] == "token-a"
    assert payload["external_response_id"] == "100"
    assert payload["duration_seconds"] == 180
    assert payload["ip"] == "10.0.0.1"
    assert payload["user_agent"] == "ua"
    assert payload["device_fingerprint"] == "dev-a"
    assert payload["raw_payload"]["municipio_votacao"] == "Sao Paulo"


def test_import_responses_uses_fallbacks_for_missing_technical_columns(tmp_path, monkeypatch):
    input_path = tmp_path / "responses.csv"
    input_path.write_text(
        "id,token,duration_seconds,municipio_votacao,attention_check\n"
        "100,token-a,90,Sao Paulo,correct\n",
        encoding="utf-8",
    )
    posted_payloads = []
    monkeypatch.setattr(
        limesurvey_import_responses,
        "post_json",
        lambda base_url, path, payload, timeout=30: posted_payloads.append(payload) or {"id": 1},
    )
    args = limesurvey_import_responses.build_parser().parse_args(
        [
            "--survey-id",
            "10",
            "--input",
            str(input_path),
            "--default-device-fingerprint",
            "ls-export",
        ]
    )

    stats = limesurvey_import_responses.import_responses(args)

    assert stats["imported"] == 1
    assert posted_payloads[0]["ip"] == "0.0.0.0"
    assert posted_payloads[0]["user_agent"] == "limesurvey-export"
    assert posted_payloads[0]["device_fingerprint"] == "ls-export"


def test_import_responses_understands_portuguese_limesurvey_columns(tmp_path, monkeypatch):
    input_path = tmp_path / "responses.csv"
    input_path.write_text(
        '"ID da resposta","Data de submissão","Código de acesso","Data de início",'
        '"Em qual município você vota?","Para controle de qualidade, digite: CORRECT",'
        '"Navegador / dispositivo","Fingerprint do dispositivo","Fuso horário","Resolução de tela"\n'
        '"5","2026-06-12 14:19:35","token_a","2026-06-12 14:19:27","Itabira","CORRECT",'
        '"Mozilla/5.0","device-123","America/Sao_Paulo","1920x1080"\n',
        encoding="utf-8",
    )
    posted_payloads = []
    monkeypatch.setattr(
        limesurvey_import_responses,
        "post_json",
        lambda base_url, path, payload, timeout=30: posted_payloads.append(payload) or {"id": 1},
    )
    args = limesurvey_import_responses.build_parser().parse_args(["--survey-id", "10", "--input", str(input_path)])

    stats = limesurvey_import_responses.import_responses(args)

    assert stats == {"imported": 1, "failed": 0}
    payload = posted_payloads[0]
    assert payload["token"] == "token_a"
    assert payload["external_response_id"] == "5"
    assert payload["duration_seconds"] == 8
    assert payload["user_agent"] == "Mozilla/5.0"
    assert payload["device_fingerprint"] == "device-123"
    assert payload["raw_payload"]["municipio_votacao"] == "Itabira"
    assert payload["raw_payload"]["attention_check"] == "CORRECT"
    assert payload["raw_payload"]["timezone"] == "America/Sao_Paulo"
    assert payload["raw_payload"]["screen_resolution"] == "1920x1080"


def test_import_responses_reports_empty_portuguese_token_column():
    args = limesurvey_import_responses.build_parser().parse_args(["--survey-id", "10", "--input", "unused.csv"])
    row = {"ID da resposta": "5", "Código de acesso": ""}

    try:
        limesurvey_import_responses.build_response_payload(row, args)
    except ValueError as exc:
        assert "Token column 'Código de acesso' is empty" in str(exc)
    else:
        raise AssertionError("Expected empty token column to fail")
