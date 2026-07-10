"""Package re-exports for db_models — one import gets everything."""

from models.db_models.base import Base
from models.db_models.user import User
from models.db_models.weather_los_angeles import WeatherLosAngeles
from models.db_models.weather_phoenix import WeatherPhoenix
from models.db_models.weather_miami import WeatherMiami
from models.db_models.weather_london import WeatherLondon

CITY_TABLE_MAP = {
    "los angeles": WeatherLosAngeles,
    "phoenix": WeatherPhoenix,
    "miami": WeatherMiami,
    "london": WeatherLondon,
}

__all__ = [
    "Base",
    "User",
    "WeatherLosAngeles",
    "WeatherPhoenix",
    "WeatherMiami",
    "WeatherLondon",
    "CITY_TABLE_MAP",
]
