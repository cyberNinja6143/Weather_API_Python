"""Response model for the extreme-heat query."""

from typing import List

from pydantic import BaseModel, Field

from models.api_models.extreme_day import ExtremeDay


class ExtremeHeatResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    extreme_day_count: int = Field(..., description="Number of days where max temp exceeded 32°C (≈90°F).")
    extreme_days: List[ExtremeDay] = Field(default_factory=list, description="Details of each extreme day.")
