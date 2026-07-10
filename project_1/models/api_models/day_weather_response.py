"""Response model for a single-day weather query."""

import datetime as _dt
from typing import Optional

from pydantic import BaseModel, Field


class DayWeatherResponse(BaseModel):
    city: str = Field(..., description="City name as stored.")
    date: _dt.date = Field(..., description="The requested date.")
    temperature_2m_max: Optional[float] = Field(None, description="Maximum temperature in °C.")
    temperature_2m_min: Optional[float] = Field(None, description="Minimum temperature in °C.")
    temperature_2m_mean: Optional[float] = Field(None, description="Mean temperature in °C.")
    precipitation_sum: Optional[float] = Field(None, description="Total precipitation in mm.")
    wind_speed_10m_max: Optional[float] = Field(None, description="Maximum wind speed in km/h.")
