from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class WeatherRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cities: List[str] = Field(..., min_length=1)
    start_date: date
    end_date: date
    daily_variables: List[str] = Field(default_factory=lambda: ["temperature_2m_max", "precipitation_sum", "wind_speed_10m_max"])
