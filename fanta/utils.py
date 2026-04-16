from __future__ import annotations

import json
import re
from typing import Any


def parse_json_safely(text: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    cleaned = re.sub(r"```json|```", "", text or "").strip()
    fallback_payload = fallback or {"error": "Could not parse", "raw": cleaned[:1000]}

    if not cleaned:
        return fallback_payload

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return fallback_payload
    return fallback_payload
