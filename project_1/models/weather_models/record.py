from datetime import date
from typing import Optional

from pydantic import BaseModel


class WeatherRecord(BaseModel):
    date: date
    city: str
    temperature_2m_max: Optional[float] = None
    precipitation_sum: Optional[float] = None
    wind_speed_10m_max: Optional[float] = None
