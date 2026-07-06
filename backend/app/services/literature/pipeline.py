from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.config import PREVIEW_ROWS
from .artifact_manager import ArtifactRecord, replace_artifact, serialize_artifact, store_artifact
from .exporter import create_screening_excel, dataframe_to_csv_bytes, write_report_text


def preview_records(dataframe: pd.DataFrame, rows: int = PREVIEW_ROWS) -> list[dict[str, Any]]:
    """Return a stable, JSON-serializable preview of the first rows."""
    return dataframe.head(rows).fillna("").to_dict(orient="records")


def build_dataset_exports(
    job_id: str,
    master_dataset: pd.DataFrame,
    deduplicated_dataset: pd.DataFrame,
    review_dataset: pd.DataFrame,
    report: dict[str, Any],
    *,
    include_master: bool = False,
) -> dict[str, ArtifactRecord]:
    """Create the export bundle for a job.

    The master dataset is only generated on the initial deduplication pass; later
    fuzzy-threshold or review regeneration reuses the existing master artifact.
    """
    artifacts: dict[str, ArtifactRecord] = {}
    if include_master:
        artifacts["master_dataset_csv"] = store_artifact(
            job_id,
            "master_dataset_csv",
            "master_dataset.csv",
            dataframe_to_csv_bytes(master_dataset.drop(columns=["normalized_title", "source_type", "record_index"], errors="ignore")),
            "text/csv",
        )

    artifacts["deduplicated_csv"] = replace_artifact(
        job_id,
        "deduplicated_csv",
        "deduplicated.csv",
        dataframe_to_csv_bytes(deduplicated_dataset.drop(columns=["normalized_title", "source_type", "record_index"], errors="ignore")),
        "text/csv",
    )
    artifacts["duplicate_review_csv"] = replace_artifact(
        job_id,
        "duplicate_review_csv",
        "duplicate_review.csv",
        dataframe_to_csv_bytes(review_dataset if not review_dataset.empty else pd.DataFrame(columns=["review_id", "left_index", "right_index", "record_a_source_database", "record_b_source_database", "record_a_title", "record_b_title", "similarity_score", "recommendation", "decision"])),
        "text/csv",
    )
    artifacts["screening_excel"] = replace_artifact(
        job_id,
        "screening_excel",
        "screening.xlsx",
        create_screening_excel(deduplicated_dataset, review_dataset),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    artifacts["processing_report"] = replace_artifact(
        job_id,
        "processing_report",
        "processing_report.txt",
        write_report_text(report).encode("utf-8"),
        "text/plain",
    )
    return artifacts


def public_artifact_payload(job_id: str, artifacts: dict[str, ArtifactRecord]) -> dict[str, dict[str, Any]]:
    return {name: serialize_artifact(job_id, artifact) for name, artifact in artifacts.items()}
