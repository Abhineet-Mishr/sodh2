from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ConversionType = Literal["RIS_TO_CSV", "NBIB_TO_CSV", "CSV_TO_RIS", "CSV_TO_NBIB"]
ReviewDecisionType = Literal["Keep A", "Keep B", "Keep Both", "Review"]


class ReviewDecisionPayload(BaseModel):
    decisions: dict[str, ReviewDecisionType] = Field(default_factory=dict)


class ThresholdUpdatePayload(BaseModel):
    fuzzy_threshold: int = Field(ge=85, le=99)


__all__ = ["ConversionType", "ReviewDecisionPayload", "ThresholdUpdatePayload", "ReviewDecisionType"]
