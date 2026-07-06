from __future__ import annotations

import csv
import io
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import rispy
except Exception:  # pragma: no cover - dependency optional only for local linting
    rispy = None

from app.core.config import MAX_UPLOAD_RECORDS

logger = logging.getLogger(__name__)


def detect_source_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".ris":
        return "RIS"
    if suffix == ".nbib":
        return "NBIB"
    if suffix == ".csv":
        return "CSV"
    raise ValueError(f"Unsupported file type: {suffix}")


def _parse_ris(text: str) -> pd.DataFrame:
    if not text.strip():
        return pd.DataFrame()
    if rispy is None:
        raise RuntimeError("rispy is required to parse RIS files")
    try:
        records = rispy.loads(text, skip_unknown_tags=False)
    except Exception as exc:
        raise ValueError("Corrupt RIS file") from exc
    return pd.DataFrame(records)


def _parse_nbib(text: str) -> pd.DataFrame:
    """Parse PubMed NBIB exports, which are line-oriented and easy to corrupt."""
    if not text.strip():
        return pd.DataFrame()
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    last_key: str | None = None
    key_pattern = re.compile(r"^([A-Z0-9]{2,6})\s*-\s?(.*)$")

    def flush_record() -> None:
        nonlocal current
        if current:
            records.append(current)
            current = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            flush_record()
            last_key = None
            continue

        match = key_pattern.match(line)
        if match:
            key = match.group(1).lower()
            value = match.group(2).strip()
            last_key = key
            if key in current and isinstance(current[key], list):
                current[key].append(value)
            elif key in current and current[key]:
                current[key] = [current[key], value]
            else:
                current[key] = value
        elif last_key:
            existing = current.get(last_key, "")
            if isinstance(existing, list):
                existing[-1] = f"{existing[-1]} {line.strip()}".strip()
            else:
                current[last_key] = f"{existing} {line.strip()}".strip()
        else:
            raise ValueError("Corrupt NBIB file")

    flush_record()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def _parse_csv(text: str) -> pd.DataFrame:
    if not text.strip():
        return pd.DataFrame()
    try:
        return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise ValueError("Corrupt CSV file") from exc


def parse_bytes(filename: str, content: bytes) -> pd.DataFrame:
    source_type = detect_source_type(filename)
    if len(content) == 0:
        return pd.DataFrame()
    if source_type == "CSV":
        dataframe = _parse_csv(content.decode("utf-8-sig", errors="replace"))
    elif source_type == "RIS":
        dataframe = _parse_ris(content.decode("utf-8-sig", errors="replace"))
    else:
        dataframe = _parse_nbib(content.decode("utf-8-sig", errors="replace"))

    if len(dataframe) > MAX_UPLOAD_RECORDS:
        raise ValueError(f"File too large: {len(dataframe)} records exceeds {MAX_UPLOAD_RECORDS}")
    return dataframe


def normalize_imported_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Light import cleanup for CSV-to-standard mapping later on."""
    if dataframe.empty:
        return dataframe
    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip().lower().replace(" ", "_") for column in dataframe.columns]
    return dataframe
