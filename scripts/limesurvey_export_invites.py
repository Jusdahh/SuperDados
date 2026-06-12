import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request


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


def _format_limesurvey_datetime(value: str | None) -> str:
    if not value:
        return ""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def build_limesurvey_participant_rows(
    invites: list[dict[str, Any]],
    *,
    email_domain: str,
    language: str,
    source_channel: str | None,
    utm_source: str | None,
    utm_campaign: str | None,
    utm_content: str | None,
) -> list[dict[str, str]]:
    rows = []
    for index, invite in enumerate(invites, start=1):
        token = invite["token"]
        rows.append(
            {
                "firstname": f"Respondente {index}",
                "lastname": "SuperDados",
                "email": f"{token}@{email_domain}",
                "emailstatus": "OK",
                "token": token,
                "usesleft": "1",
                "language": language,
                "validuntil": _format_limesurvey_datetime(invite.get("expires_at")),
                "attribute_1": str(invite["id"]),
                "attribute_2": source_channel or "",
                "attribute_3": utm_source or "",
                "attribute_4": utm_campaign or "",
                "attribute_5": utm_content or "",
            }
        )
    return rows


def write_participants_csv(output_path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "firstname",
        "lastname",
        "email",
        "emailstatus",
        "token",
        "usesleft",
        "language",
        "validuntil",
        "attribute_1",
        "attribute_2",
        "attribute_3",
        "attribute_4",
        "attribute_5",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_invites(args: argparse.Namespace) -> list[dict[str, str]]:
    payload = {
        "quantity": args.quantity,
        "source_channel": args.source_channel,
        "utm_source": args.utm_source,
        "utm_campaign": args.utm_campaign,
        "utm_content": args.utm_content,
        "expires_in_hours": args.expires_in_hours,
    }
    data = post_json(args.base_url, f"/surveys/{args.survey_id}/invites", payload, timeout=args.timeout)
    rows = build_limesurvey_participant_rows(
        data["invites"],
        email_domain=args.email_domain,
        language=args.language,
        source_channel=args.source_channel,
        utm_source=args.utm_source,
        utm_campaign=args.utm_campaign,
        utm_content=args.utm_content,
    )
    write_participants_csv(Path(args.output), rows)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export SuperDados invites as a LimeSurvey participant CSV.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="SuperDados API base URL.")
    parser.add_argument("--survey-id", type=int, required=True, help="Internal SuperDados survey id.")
    parser.add_argument("--quantity", type=int, required=True, help="Number of invites to create.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    parser.add_argument("--source-channel", default=None)
    parser.add_argument("--utm-source", default=None)
    parser.add_argument("--utm-campaign", default=None)
    parser.add_argument("--utm-content", default=None)
    parser.add_argument("--expires-in-hours", type=int, default=None)
    parser.add_argument("--language", default="", help="LimeSurvey language code. Leave blank to use survey default.")
    parser.add_argument("--email-domain", default="invalid.superdados.local")
    parser.add_argument("--timeout", type=int, default=30)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = export_invites(args)
    print(f"Wrote {len(rows)} LimeSurvey participant rows to {args.output}")


if __name__ == "__main__":
    main()
