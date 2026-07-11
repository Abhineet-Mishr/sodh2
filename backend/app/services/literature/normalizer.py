from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import pandas as pd

from app.core.config import STANDARD_FIELDS


_TITLE_CLEAN_RE = re.compile(r"[.,:;]+")
_SPACE_RE = re.compile(r"\s+")
_CSV_FIELD_ALIASES = {
    "title": "title",
    "article_title": "title",
    "ti": "title",
    "authors": "authors",
    "author": "authors",
    "au": "authors",
    "year": "year",
    "publication_year": "year",
    "dp": "year",
    "journal": "journal",
    "source": "journal",
    "journal_name": "journal",
    "jt": "journal",
    "doi": "doi",
    "aid": "doi",
    "abstract": "abstract",
    "ab": "abstract",
    "keywords": "keywords",
    "keyword": "keywords",
    "kw": "keywords",
    "ot": "keywords",
    "pmid": "pmid",
    "pubmed_id": "pmid",
    "db": "source_database",
    "source_database": "source_database",
    "database_source": "source_database",
}


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if isinstance(value, list):
        return "; ".join(_to_text(item) for item in value if _to_text(item))
    return str(value).strip()


def _split_authors(value: Any) -> str:
    text = _to_text(value)
    if not text:
        return ""
    if "||" in text:
        parts = [part.strip() for part in text.split("||") if part.strip()]
        return "; ".join(parts)
    if ";" in text:
        return "; ".join(part.strip() for part in text.split(";") if part.strip())
    if " and " in text:
        return "; ".join(part.strip() for part in text.split(" and ") if part.strip())
    return text


def normalize_year(value: Any) -> str:
    text = _to_text(value)
    if not text:
        return ""
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return match.group(0)
    return text[:4] if len(text) >= 4 else text


def normalize_title_for_deduplication(title: Any) -> str:
    text = _to_text(title).lower()
    text = _TITLE_CLEAN_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text)
    return text.strip()


def standardize_dataframe(raw_dataframe: pd.DataFrame, source_database: str, source_type: str) -> pd.DataFrame:
    """Map an imported dataframe to the standard schema used across the toolkit."""
    if raw_dataframe is None or raw_dataframe.empty:
        return pd.DataFrame(columns=STANDARD_FIELDS)

    dataframe = raw_dataframe.copy()
    dataframe.columns = [str(column).strip().lower().replace(" ", "_") for column in dataframe.columns]
    for column in list(dataframe.columns):
        alias = _CSV_FIELD_ALIASES.get(column)
        if alias and alias != column:
            dataframe[alias] = dataframe[column]

    for required_column in STANDARD_FIELDS:
        if required_column not in dataframe.columns:
            dataframe[required_column] = ""

    dataframe["title"] = dataframe["title"].map(_to_text)
    dataframe["authors"] = dataframe["authors"].map(_split_authors)
    dataframe["year"] = dataframe["year"].map(normalize_year)
    dataframe["journal"] = dataframe["journal"].map(_to_text)
    dataframe["doi"] = dataframe["doi"].map(_to_text).str.lower().str.strip()
    dataframe["abstract"] = dataframe["abstract"].map(_to_text)
    dataframe["keywords"] = dataframe["keywords"].map(_to_text)
    dataframe["pmid"] = dataframe["pmid"].map(_to_text)
    if "source_database" in dataframe.columns and dataframe["source_database"].fillna("").astype(str).str.strip().ne("").any():
        dataframe["source_database"] = dataframe["source_database"].map(_to_text)
    else:
        dataframe["source_database"] = source_database or source_type.upper()

    ordered = dataframe[STANDARD_FIELDS].copy()
    ordered["normalized_title"] = ordered["title"].map(normalize_title_for_deduplication)
    ordered["source_type"] = source_type
    ordered["record_index"] = range(1, len(ordered) + 1)
    return ordered


def ensure_text_columns(dataframe: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = dataframe.copy()
    for column in columns:
        if column not in result.columns:
            result[column] = ""
        result[column] = result[column].fillna("").astype(str)
    return result
