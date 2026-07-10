"""Integration tests for services/weather_analytics.py — all 7 query methods.

Seeds known test data then asserts computed results.  Run standalone::

    python tests/test_weather_analytics.py
"""

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from services.weather_analytics import (
    get_day,
    get_extreme_heat_days,
    get_hottest_in_month,
    get_hottest_in_year,
    get_month_summary,
    get_monthly_rainfall,
    get_year_summary,
)
from tests.test_conftest import seeded_weather_data  # noqa: F401


def test_get_day_returns_record(seeded_weather_data) -> None:  # noqa: F811
    """Fetch a specific day and assert its temperature values."""
    result = get_day(seeded_weather_data, "phoenix", date(2025, 6, 2))
    assert result.city == "phoenix"
    assert result.date == date(2025, 6, 2)
    assert result.temperature_2m_max == pytest.approx(22.0)


def test_get_month_summary(seeded_weather_data) -> None:  # noqa: F811
    """Monthly summary aggregates match the seeded data."""
    result = get_month_summary(seeded_weather_data, "phoenix", 2025, 6)
    assert result.record_count == 5
    assert result.avg_temp_max is not None
    assert result.total_precipitation is not None


def test_get_year_summary(seeded_weather_data) -> None:  # noqa: F811
    """Year summary aggregates match the seeded data."""
    result = get_year_summary(seeded_weather_data, "phoenix", 2025)
    assert result.record_count == 5
    assert result.avg_temp_max is not None


def test_get_hottest_in_month(seeded_weather_data) -> None:  # noqa: F811
    """Hottest day in June should be the last seeded day (highest temp)."""
    result = get_hottest_in_month(seeded_weather_data, "phoenix", 2025, 6)
    assert result.date == date(2025, 6, 5)  # day 5 has the highest temp: 20+4*2=28


def test_get_hottest_in_year(seeded_weather_data) -> None:  # noqa: F811
    """Hottest day in 2025 should be the last seeded day."""
    result = get_hottest_in_year(seeded_weather_data, "phoenix", 2025)
    assert result.date == date(2025, 6, 5)


def test_get_monthly_rainfall(seeded_weather_data) -> None:  # noqa: F811
    """Average rainfall matches seeded precip values (0, 1.5, 3.0, 4.5, 6.0)."""
    result = get_monthly_rainfall(seeded_weather_data, "phoenix", 2025, 6)
    # Average of 0, 1.5, 3, 4.5, 6 = 3.0
    assert result.avg_precipitation_mm == pytest.approx(3.0)


def test_get_extreme_heat_days(seeded_weather_data) -> None:  # noqa: F811
    """No seeded days exceed 32°C — extreme count should be 0."""
    result = get_extreme_heat_days(seeded_weather_data, "phoenix", 2025, 6)
    assert result.extreme_day_count == 0
    assert result.extreme_days == []


def test_unsupported_city_raises(seeded_weather_data) -> None:  # noqa: F811
    """Passing an unknown city raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported city"):
        get_day(seeded_weather_data, "atlantis", date(2025, 6, 1))


# -- standalone runner ----------------------------------------------------------

def _run(name: str, fn, db) -> None:
    print(f"\n=== {name} ===")
    try:
        fn(db)
        print("PASS")
    except Exception as exc:
        print(f"FAIL: {exc}")


if __name__ == "__main__":
    print("Running weather analytics tests...\n")
    from tests.test_conftest import TestSessionLocal, _engine, CITIES, _insert_weather_rows
    from models.db_models import Base, CITY_TABLE_MAP
    from sqlalchemy import text

    Base.metadata.create_all(bind=_engine)
    session = TestSessionLocal()
    start = date(2025, 6, 1)
    for city in CITIES:
        _insert_weather_rows(session, city, start, rows=5)
    try:
        _run("test_get_day_returns_record", test_get_day_returns_record, session)
        _run("test_get_month_summary", test_get_month_summary, session)
        _run("test_get_year_summary", test_get_year_summary, session)
        _run("test_get_hottest_in_month", test_get_hottest_in_month, session)
        _run("test_get_hottest_in_year", test_get_hottest_in_year, session)
        _run("test_get_monthly_rainfall", test_get_monthly_rainfall, session)
        _run("test_get_extreme_heat_days", test_get_extreme_heat_days, session)
        _run("test_unsupported_city_raises", test_unsupported_city_raises, session)
        session.rollback()
        # Remove any test rows that may exist from previous runs.
        for model in CITY_TABLE_MAP.values():
            session.execute(text(f"DELETE FROM {model.__tablename__}"))
        session.commit()
    finally:
        session.close()
    print("\nWeather analytics tests completed.")
