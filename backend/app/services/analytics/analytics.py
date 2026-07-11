from __future__ import annotations

from typing import Any

import pandas as pd


def generate_counts(master_dataset: pd.DataFrame, deduplicated_dataset: pd.DataFrame) -> dict[str, Any]:
    source_counts = (
        master_dataset.get("source_database", pd.Series(dtype=str))
        .fillna("")
        .astype(str)
        .value_counts()
        .to_dict()
    )
    return {
        "records_imported": int(len(master_dataset)),
        "final_records": int(len(deduplicated_dataset)),
        "source_counts": source_counts,
        "prisma": {
            "identified": int(len(master_dataset)),
            "after_screening": int(len(deduplicated_dataset)),
        },
    }
