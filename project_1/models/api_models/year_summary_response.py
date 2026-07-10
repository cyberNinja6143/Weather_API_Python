"""Response model for a yearly weather summary."""

from typing import Optional

from pydantic import BaseModel, Field


class YearSummaryResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    year: int = Field(..., ge=2000, le=2100)
    avg_temp_max: Optional[float] = Field(None)
    avg_temp_min: Optional[float] = Field(None)
    avg_temp_mean: Optional[float] = Field(None)
    total_precipitation: Optional[float] = Field(None)
    avg_wind_speed: Optional[float] = Field(None)
    record_count: int = Field(..., description="Number of daily records in the year.")
