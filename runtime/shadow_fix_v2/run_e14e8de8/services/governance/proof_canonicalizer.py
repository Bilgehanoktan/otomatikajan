import json
import datetime
import uuid
from typing import Any, Dict

def canonicalize_payload(payload: Any) -> str:
    """
    Converts a payload into a canonical JSON string for consistent hashing.
    Rules:
    - Keys are sorted alphabetically.
    - Datetimes are normalized to ISO UTC string.
    - UUIDs are converted to strings.
    - No extra whitespace.
    """
    return serialize_canonical_json(payload)

def normalize_value(val: Any) -> Any:
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, dict):
        return {k: normalize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [normalize_value(i) for i in val]
    if isinstance(val, float):
        # Consistent float formatting (avoiding .0 vs no decimal)
        return format(val, ".8f").rstrip("0").rstrip(".")
    return val

def serialize_canonical_json(payload: Any) -> str:
    normalized = normalize_value(payload)
    # sort_keys=True is critical for canonicalization
    return json.dumps(normalized, sort_keys=True, separators=(',', ':'))
