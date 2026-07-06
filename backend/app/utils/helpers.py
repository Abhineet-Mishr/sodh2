from __future__ import annotations

from typing import Any

ARTIFACT_LIFETIMES = {
    30: "30 min",
    60: "1 hr",
    120: "2 hr",
    180: "3 hr",
    360: "6 hr",
    720: "12 hr",
    1440: "24 hr",
}


def parse_artifact_lifetime_minutes(value: Any, default: int = 30) -> int:
    """Coerce a submitted lifetime value to one of the supported minute options."""
    try:
        minutes = int(value)
    except Exception:
        return default
    return minutes if minutes in ARTIFACT_LIFETIMES else default


def parse_fuzzy_threshold(value: Any, default: int = 90) -> int:
    """Coerce a fuzzy threshold to the supported 85-99 range."""
    try:
        threshold = int(value)
    except Exception:
        return default
    return threshold if 85 <= threshold <= 99 else default
