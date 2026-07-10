"""Response model for a monthly weather summary."""

from typing import Optional

from pydantic import BaseModel, Field


class MonthSummaryResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    avg_temp_max: Optional[float] = Field(None, description="Average of daily max temperatures.")
    avg_temp_min: Optional[float] = Field(None, description="Average of daily min temperatures.")
    avg_temp_mean: Optional[float] = Field(None, description="Average of daily mean temperatures.")
    total_precipitation: Optional[float] = Field(None, description="Sum of daily precipitation.")
    avg_wind_speed: Optional[float] = Field(None, description="Average of daily max wind speeds.")
    record_count: int = Field(..., description="Number of daily records in the month.")
