from pathlib import Path
import os

import psycopg2
from dotenv import load_dotenv


def connect_to_weather_db():
    """Create a PostgreSQL connection using credentials from the local .env file."""
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "WeatherAPI")

    if not db_user or not db_password:
        raise ValueError("Database credentials are missing. Set DB_USER and DB_PASSWORD in .env.")

    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )
