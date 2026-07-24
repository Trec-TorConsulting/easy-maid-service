from __future__ import annotations


def _str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clean_quote_request_payload(payload: dict) -> dict:
    cleaned = {
        "full_name": _str(payload.get("full_name") or payload.get("name")),
        "email": _str(payload.get("email")),
        "phone": _str(payload.get("phone")),
        "address": _str(payload.get("address")),
        "city": _str(payload.get("city")),
        "state": _str(payload.get("state") or "NJ"),
        "details": _str(payload.get("details")),
        "is_honeypot": bool(_str(payload.get("website"))),
    }

    required = ["full_name", "email", "address", "city", "details"]
    missing = [field for field in required if not cleaned[field]]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required fields: {missing_text}")

    if "@" not in cleaned["email"]:
        raise ValueError("A valid email is required")

    return cleaned
