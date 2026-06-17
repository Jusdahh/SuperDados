import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request


TOKEN_COLUMN_ALIASES = ("token", "Token", "Código de acesso", "Codigo de acesso", "access code", "Access code")
RESPONSE_ID_COLUMN_ALIASES = ("id", "ID da resposta", "Response ID", "response_id")
STARTED_AT_COLUMN_ALIASES = ("startdate", "Data de início", "Data de inicio")
SUBMITTED_AT_COLUMN_ALIASES = ("submitdate", "datestamp", "Data de submissão", "Data de submissao")
CITY_COLUMN_ALIASES = ("municipio_votacao", "Em qual município você vota?", "Em qual municipio voce vota?")
ATTENTION_COLUMN_ALIASES = (
    "attention_check",
    "Para controle de qualidade, digite: CORRECT",
    "Para controle de qualidade, digite correct.",
)
IP_COLUMN_ALIASES = ("ipaddr", "IP address", "Endereço IP", "Endereco IP")
USER_AGENT_COLUMN_ALIASES = ("user_agent", "User agent", "Navegador / dispositivo", "Agente de usuario")
DEVICE_FINGERPRINT_COLUMN_ALIASES = ("device_fingerprint", "Device fingerprint", "Fingerprint do dispositivo")
TRACE_FIELD_ALIASES = {
    "user_agent": USER_AGENT_COLUMN_ALIASES,
    "device_fingerprint": DEVICE_FINGERPRINT_COLUMN_ALIASES,
    "browser_language": ("browser_language", "Idioma do navegador"),
    "timezone": ("timezone", "Fuso horario", "Fuso horário"),
    "screen_resolution": ("screen_resolution", "Resolucao de tela", "Resolução de tela"),
    "referrer": ("referrer", "URL de origem", "Origem do acesso"),
}


def post_json(base_url: str, path: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise RuntimeError(f"POST {url} failed with HTTP {exc.code}: {details}") from exc


def first_present(row: dict[str, str], columns: tuple[str, ...]) -> str | None:
    for column in columns:
        if column in row:
            return column
    return None


def value_from(row: dict[str, str], preferred: str, aliases: tuple[str, ...]) -> tuple[str | None, str | None]:
    columns = (preferred, *aliases)
    column = first_present(row, columns)
    if column is None:
        return None, None
    return column, row.get(column)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None


def infer_duration_seconds(
    row: dict[str, str],
    *,
    duration_column: str,
    started_at_column: str,
    submitted_at_column: str,
) -> int | None:
    explicit_duration = row.get(duration_column)
    if explicit_duration:
        try:
            return int(float(explicit_duration))
        except ValueError:
            return None

    _, started_at_value = value_from(row, started_at_column, STARTED_AT_COLUMN_ALIASES)
    _, submitted_at_value = value_from(row, submitted_at_column, SUBMITTED_AT_COLUMN_ALIASES)
    started_at = parse_datetime(started_at_value)
    submitted_at = parse_datetime(submitted_at_value)
    if started_at and submitted_at:
        seconds = int((submitted_at - started_at).total_seconds())
        return seconds if seconds >= 0 else None
    return None


def normalized_raw_payload(row: dict[str, str]) -> dict[str, str]:
    raw_payload = dict(row)
    _, city = value_from(row, "municipio_votacao", CITY_COLUMN_ALIASES)
    _, attention_check = value_from(row, "attention_check", ATTENTION_COLUMN_ALIASES)
    if city and "municipio_votacao" not in raw_payload:
        raw_payload["municipio_votacao"] = city
    if attention_check and "attention_check" not in raw_payload:
        raw_payload["attention_check"] = attention_check
    for normalized_name, aliases in TRACE_FIELD_ALIASES.items():
        _, value = value_from(row, normalized_name, aliases)
        if value and normalized_name not in raw_payload:
            raw_payload[normalized_name] = value
    return raw_payload


def build_response_payload(row: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    token_column, token = value_from(row, args.token_column, TOKEN_COLUMN_ALIASES)
    if token_column is None:
        raise ValueError(f"Missing token column. Tried: {', '.join((args.token_column, *TOKEN_COLUMN_ALIASES))}")
    if not token:
        raise ValueError(
            f"Token column '{token_column}' is empty. In LimeSurvey, turn off anonymized responses or export tokens."
        )

    _, external_response_id = value_from(row, args.response_id_column, RESPONSE_ID_COLUMN_ALIASES)
    submitted_at_column, _ = value_from(row, args.submitted_at_column, SUBMITTED_AT_COLUMN_ALIASES)
    submitted_at_column = submitted_at_column or args.submitted_at_column

    return {
        "survey_id": args.survey_id,
        "token": token,
        "external_response_id": external_response_id,
        "duration_seconds": infer_duration_seconds(
            row,
            duration_column=args.duration_column,
            started_at_column=args.started_at_column,
            submitted_at_column=submitted_at_column,
        ),
        "ip": value_from(row, args.ip_column, IP_COLUMN_ALIASES)[1] or args.default_ip,
        "user_agent": value_from(row, args.user_agent_column, USER_AGENT_COLUMN_ALIASES)[1] or args.default_user_agent,
        "device_fingerprint": (
            value_from(row, args.device_fingerprint_column, DEVICE_FINGERPRINT_COLUMN_ALIASES)[1]
            or args.default_device_fingerprint
        ),
        "raw_payload": normalized_raw_payload(row),
    }


def import_responses(args: argparse.Namespace) -> dict[str, int]:
    stats = {"imported": 0, "failed": 0}
    with Path(args.input).open(newline="", encoding=args.encoding) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=args.delimiter)
        for line_number, row in enumerate(reader, start=2):
            try:
                payload = build_response_payload(row, args)
                post_json(args.base_url, "/responses/import", payload, timeout=args.timeout)
                stats["imported"] += 1
            except Exception as exc:
                stats["failed"] += 1
                print(f"Line {line_number}: {exc}")
                if args.fail_fast:
                    raise
    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import LimeSurvey exported CSV responses into SuperDados.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="SuperDados API base URL.")
    parser.add_argument("--survey-id", type=int, required=True, help="Internal SuperDados survey id.")
    parser.add_argument("--input", required=True, help="LimeSurvey exported responses CSV path.")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--token-column", default="token")
    parser.add_argument("--response-id-column", default="id")
    parser.add_argument("--duration-column", default="duration_seconds")
    parser.add_argument("--started-at-column", default="startdate")
    parser.add_argument("--submitted-at-column", default="submitdate")
    parser.add_argument("--ip-column", default="ipaddr")
    parser.add_argument("--user-agent-column", default="user_agent")
    parser.add_argument("--device-fingerprint-column", default="device_fingerprint")
    parser.add_argument("--default-ip", default="0.0.0.0")
    parser.add_argument("--default-user-agent", default="limesurvey-export")
    parser.add_argument("--default-device-fingerprint", default=None)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    stats = import_responses(args)
    print(f"Imported {stats['imported']} responses; {stats['failed']} failed")


if __name__ == "__main__":
    main()
