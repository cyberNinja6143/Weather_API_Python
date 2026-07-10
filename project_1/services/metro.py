import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from services.city_coordinates import CityCoordinates
from models.weather_models import WeatherRequest, WeatherResponse, WeatherRecord


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

metro_url = os.getenv("OPEN_METEO_ARCHIVE_URL")

app = FastAPI(title="Weather API")


class MetroWeatherService:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or os.getenv("OPEN_METEO_ARCHIVE_URL", metro_url)

    def fetch_weather(self, cities: List[str], start_date: date, end_date: date, daily_variables: Optional[List[str]] = None) -> List[WeatherResponse]:
        if not cities:
            raise ValueError("At least one city is required.")

        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date.")

        if daily_variables is None:
            daily_variables = ["temperature_2m_max", "precipitation_sum", "wind_speed_10m_max"]

        responses: List[WeatherResponse] = []
        for city in cities:
            params = {
                "latitude": CityCoordinates.latitude(city),
                "longitude": CityCoordinates.longitude(city),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "daily": ",".join(daily_variables),
                "timezone": "auto",
            }
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            daily = payload.get("daily", {})
            dates = daily.get("time", [])
            records: List[WeatherRecord] = []
            for index, day in enumerate(dates):
                records.append(
                    WeatherRecord(
                        date=datetime.strptime(day, "%Y-%m-%d").date(),
                        city=city,
                        temperature_2m_max=self._safe_value(daily.get("temperature_2m_max"), index),
                        precipitation_sum=self._safe_value(daily.get("precipitation_sum"), index),
                        wind_speed_10m_max=self._safe_value(daily.get("wind_speed_10m_max"), index),
                    )
                )
            responses.append(
                WeatherResponse(
                    city=city,
                    start_date=start_date,
                    end_date=end_date,
                    records=records,
                )
            )
        return responses

    @staticmethod
    def _safe_value(values, index: int):
        if isinstance(values, list) and index < len(values):
            return values[index]
        return None


service = MetroWeatherService()


@app.post("/weather", response_model=List[WeatherResponse])
def get_weather(request: WeatherRequest):
    try:
        return service.fetch_weather(
            cities=request.cities,
            start_date=request.start_date,
            end_date=request.end_date,
            daily_variables=request.daily_variables,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Weather service request failed: {exc}") from exc
