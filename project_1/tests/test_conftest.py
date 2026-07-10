"""Shared test fixtures for the weather analytics test suite.

Usage in a test file::

    from tests.test_conftest import test_db_session, test_client, seeded_weather_data
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Ensure the project root is on sys.path so package imports resolve.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.db_models import Base  # noqa: E402
from main import app  # noqa: E402

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME', 'WeatherAPI')}",
)

_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def test_db_session() -> Generator[Session, None, None]:
    """Create a fresh database session wrapped in a transaction that rolls back."""
    Base.metadata.create_all(bind=_engine)
    db = TestSessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with the DB dependency overridden to use the test session."""
    from services.db_session import get_db

    def _override_get_db() -> Generator[Session, None, None]:
        yield test_db_session

    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


CITIES = ["los angeles", "phoenix", "miami", "london"]


def _insert_weather_rows(db: Session, city: str, base_date: date, rows: int = 5) -> None:
    """Insert *rows* consecutive daily records for *city* starting at *base_date*."""
    from models.db_models import CITY_TABLE_MAP

    table_name = CITY_TABLE_MAP[city].__tablename__
    for i in range(rows):
        d = base_date + timedelta(days=i)
        db.execute(
            text(
                f"INSERT INTO {table_name} (date, temperature_2m_max, temperature_2m_min, "
                f"temperature_2m_mean, precipitation_sum, wind_speed_10m_max) "
                f"VALUES (:d, :tmax, :tmin, :tmean, :precip, :wind) "
                f"ON CONFLICT (date) DO NOTHING"
            ),
            {
                "d": d.isoformat(),
                "tmax": 20.0 + i * 2,
                "tmin": 10.0 + i,
                "tmean": 15.0 + i * 1.5,
                "precip": i * 1.5,
                "wind": 10.0 + i,
            },
        )
    db.flush()


@pytest.fixture(scope="function")
def seeded_weather_data(test_db_session: Session) -> Session:
    """Insert test weather data into all four city tables and return the session."""
    start = date(2025, 6, 1)
    for city in CITIES:
        _insert_weather_rows(test_db_session, city, start, rows=5)
    return test_db_session
