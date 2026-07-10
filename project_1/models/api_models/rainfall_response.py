"""Response model for the monthly rainfall query."""

from typing import Optional

from pydantic import BaseModel, Field


class RainfallResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    avg_precipitation_mm: Optional[float] = Field(None, description="Average daily precipitation in mm.")
