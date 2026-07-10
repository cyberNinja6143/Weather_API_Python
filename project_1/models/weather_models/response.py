from datetime import date
from typing import List

from pydantic import BaseModel

from models.weather_models.record import WeatherRecord


class WeatherResponse(BaseModel):
    city: str
    start_date: date
    end_date: date
    records: List[WeatherRecord]
