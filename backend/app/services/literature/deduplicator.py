from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import pandas as pd
from rapidfuzz import fuzz

from app.services.literature.normalizer import normalize_title_for_deduplication


@dataclass
class DeduplicationStage:
    name: str
    removed: int
    remaining: int


def _prepare(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy().reset_index(drop=True)
    if "normalized_title" not in result.columns:
        result["normalized_title"] = result["title"].map(normalize_title_for_deduplication)
    if "doi" not in result.columns:
        result["doi"] = ""
    if "pmid" not in result.columns:
        result["pmid"] = ""
    if "title" not in result.columns:
        result["title"] = ""
    result["doi"] = result["doi"].fillna("").astype(str).str.lower().str.strip()
    result["pmid"] = result["pmid"].fillna("").astype(str).str.strip()
    result["title"] = result["title"].fillna("").astype(str)
    return result


def _drop_exact_matches(dataframe: pd.DataFrame, column: str) -> tuple[pd.DataFrame, int]:
    if column not in dataframe.columns:
        return dataframe.copy(), 0
    seen: set[str] = set()
    keep_indices: list[int] = []
    removed = 0
    for index, value in enumerate(dataframe[column].fillna("").astype(str)):
        if not value:
            keep_indices.append(index)
            continue
        if value in seen:
            removed += 1
            continue
        seen.add(value)
        keep_indices.append(index)
    return dataframe.iloc[keep_indices].reset_index(drop=True), removed


def _drop_exact_title_matches(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    seen: set[str] = set()
    keep_indices: list[int] = []
    removed = 0
    for index, value in enumerate(dataframe["normalized_title"].fillna("").astype(str)):
        if not value:
            keep_indices.append(index)
            continue
        if value in seen:
            removed += 1
            continue
        seen.add(value)
        keep_indices.append(index)
    return dataframe.iloc[keep_indices].reset_index(drop=True), removed


def _blocking_key(row: pd.Series) -> str:
    title = str(row.get("normalized_title", "")).strip()
    year = str(row.get("year", "")).strip()
    first_word = title.split(" ", 1)[0] if title else ""
    return f"{year}:{first_word[:8]}"


def _collect_fuzzy_candidates(dataframe: pd.DataFrame, minimum_score: int) -> list[tuple[int, int, int, str, str]]:
    """Return candidate pairs only within light title/year blocks.

    This avoids the quadratic cost of comparing every record with every other
    record while still catching the common systematic-review duplicates.
    """
    buckets: dict[str, list[int]] = defaultdict(list)
    for index, row in dataframe.iterrows():
        buckets[_blocking_key(row)].append(index)

    candidates: list[tuple[int, int, int, str, str]] = []
    for indices in buckets.values():
        if len(indices) < 2:
            continue
        for left_index, right_index in combinations(indices, 2):
            left_title = str(dataframe.at[left_index, "normalized_title"])
            right_title = str(dataframe.at[right_index, "normalized_title"])
            if not left_title or not right_title:
                continue
            score = fuzz.token_set_ratio(left_title, right_title)
            if score >= minimum_score:
                candidates.append((left_index, right_index, int(score), left_title, right_title))
    return candidates


def _build_review_rows(after_title: pd.DataFrame, minimum_score: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    review_rows: list[dict[str, Any]] = []
    auto_removed_indices: set[int] = set()
    for left_index, right_index, score, left_title, right_title in _collect_fuzzy_candidates(after_title, minimum_score):
        recommendation = "Review"
        if score >= 98:
            recommendation = "Keep A"
            auto_removed_indices.add(right_index)
        review_rows.append(
            {
                "review_id": f"{left_index}-{right_index}",
                "left_index": left_index,
                "right_index": right_index,
                "record_a_id": str(left_index),
                "record_b_id": str(right_index),
                "record_a_source_database": str(after_title.at[left_index, "source_database"]),
                "record_b_source_database": str(after_title.at[right_index, "source_database"]),
                "record_a_title": left_title,
                "record_b_title": right_title,
                "similarity_score": score,
                "recommendation": recommendation,
                "decision": recommendation,
            }
        )

    if auto_removed_indices:
        kept_mask = [index not in auto_removed_indices for index in range(len(after_title))]
        after_fuzzy = after_title.loc[kept_mask].reset_index(drop=True)
        removed_fuzzy = len(after_title) - len(after_fuzzy)
    else:
        after_fuzzy = after_title.copy().reset_index(drop=True)
        removed_fuzzy = 0

    review_dataset = pd.DataFrame(review_rows)
    return after_fuzzy, review_dataset, removed_fuzzy


def recompute_fuzzy_stage(after_title: pd.DataFrame, minimum_score: int = 90) -> dict[str, Any]:
    """Recompute only the fuzzy stage from an already exact-title-deduped dataset."""
    staged = after_title.copy().reset_index(drop=True)
    after_fuzzy, review_dataset, removed_fuzzy = _build_review_rows(staged, minimum_score)
    report = {
        "records_after_exact_title": int(len(staged)),
        "records_after_fuzzy": int(len(after_fuzzy)),
        "final_records": int(len(after_fuzzy)),
        "removed_by_fuzzy": int(removed_fuzzy),
        "fuzzy_threshold": int(minimum_score),
    }
    return {
        "deduplicated_dataset": after_fuzzy,
        "review_dataset": review_dataset,
        "report": report,
    }


def deduplicate_records(dataframe: pd.DataFrame, minimum_score: int = 90) -> dict[str, Any]:
    working = _prepare(dataframe)
    stages: list[DeduplicationStage] = []

    after_doi, removed_doi = _drop_exact_matches(working, "doi")
    stages.append(DeduplicationStage("doi", removed_doi, len(after_doi)))

    after_pmid, removed_pmid = _drop_exact_matches(after_doi, "pmid")
    stages.append(DeduplicationStage("pmid", removed_pmid, len(after_pmid)))

    after_title, removed_title = _drop_exact_title_matches(after_pmid)
    stages.append(DeduplicationStage("exact_title", removed_title, len(after_title)))

    fuzzy_stage = _build_review_rows(after_title, minimum_score)
    after_fuzzy, review_dataset, removed_fuzzy = fuzzy_stage

    stages.append(DeduplicationStage("fuzzy", removed_fuzzy, len(after_fuzzy)))

    report = {
        "records_imported": int(len(working)),
        "records_after_doi": int(len(after_doi)),
        "records_after_pmid": int(len(after_pmid)),
        "records_after_exact_title": int(len(after_title)),
        "records_after_fuzzy": int(len(after_fuzzy)),
        "final_records": int(len(after_fuzzy)),
        "removed_by_doi": int(removed_doi),
        "removed_by_pmid": int(removed_pmid),
        "removed_by_exact_title": int(removed_title),
        "removed_by_fuzzy": int(removed_fuzzy),
        "fuzzy_threshold": int(minimum_score),
        "stages": [stage.__dict__ for stage in stages],
    }

    return {
        "master_dataset": working,
        "exact_title_dataset": after_title,
        "deduplicated_dataset": after_fuzzy,
        "review_dataset": review_dataset,
        "report": report,
    }


def apply_review_decisions(
    exact_title_dataset: pd.DataFrame,
    review_dataset: pd.DataFrame,
    decisions: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Apply reviewer choices without rerunning earlier deduplication stages."""
    decisions = decisions or {}
    review_dataset = review_dataset.copy().reset_index(drop=True)

    applied_decisions: list[str] = []
    excluded_indices: set[int] = set()
    unresolved_rows = 0

    for row in review_dataset.itertuples(index=False):
        review_id = str(getattr(row, "review_id"))
        decision = decisions.get(review_id) or str(getattr(row, "decision", "") or getattr(row, "recommendation", "Review"))
        applied_decisions.append(decision)

        left_index = int(getattr(row, "left_index"))
        right_index = int(getattr(row, "right_index"))

        if decision == "Keep A":
            excluded_indices.add(right_index)
        elif decision == "Keep B":
            excluded_indices.add(left_index)
        elif decision == "Keep Both":
            continue
        else:
            unresolved_rows += 1

    finalized_dataset = exact_title_dataset.drop(index=list(excluded_indices), errors="ignore").reset_index(drop=True)
    review_dataset["decision"] = applied_decisions
    report = {
        "records_after_review": int(len(finalized_dataset)),
        "final_records": int(len(finalized_dataset)),
        "removed_by_reviewer": int(len(excluded_indices)),
        "review_decisions_saved": int(sum(1 for decision in applied_decisions if decision != "Review")),
        "review_unresolved": int(unresolved_rows),
    }
    return finalized_dataset, review_dataset, report
