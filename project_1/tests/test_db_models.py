"""Integration tests for the SQLAlchemy database models.

Requires a running PostgreSQL instance.  Run standalone::

    python tests/test_db_models.py
"""

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import inspect, text

from tests.test_conftest import test_db_session  # noqa: F401 — fixture used by tests


def test_user_table_exists(test_db_session) -> None:  # noqa: F811
    """The 'users' table is present in the database."""
    inspector = inspect(test_db_session.get_bind())
    tables = inspector.get_table_names()
    assert "users" in tables


def test_city_tables_exist(test_db_session) -> None:  # noqa: F811
    """All four city weather tables are present."""
    inspector = inspect(test_db_session.get_bind())
    tables = inspector.get_table_names()
    for expected in ("weather_los_angeles", "weather_phoenix", "weather_miami", "weather_london"):
        assert expected in tables, f"Missing table: {expected}"


def test_user_insert_and_query(test_db_session) -> None:  # noqa: F811
    """Insert a User row and fetch it back."""
    from models.db_models import User

    user = User(username="testuser", password_hash="hashed_value")
    test_db_session.add(user)
    test_db_session.flush()

    fetched = test_db_session.query(User).filter(User.username == "testuser").first()
    assert fetched is not None
    assert fetched.username == "testuser"
    assert fetched.password_hash == "hashed_value"


def test_weather_insert_and_query(test_db_session) -> None:  # noqa: F811
    """Insert a row into weather_phoenix and read it back."""
    from models.db_models import WeatherPhoenix

    row = WeatherPhoenix(
        date=date(2025, 3, 15),
        temperature_2m_max=28.5,
        temperature_2m_min=18.0,
        temperature_2m_mean=23.25,
        precipitation_sum=0.0,
        wind_speed_10m_max=14.2,
    )
    test_db_session.add(row)
    test_db_session.flush()

    fetched = test_db_session.query(WeatherPhoenix).filter(WeatherPhoenix.date == date(2025, 3, 15)).first()
    assert fetched is not None
    assert fetched.temperature_2m_max == 28.5


def test_city_table_map_keys(test_db_session) -> None:  # noqa: F811
    """CITY_TABLE_MAP contains the expected normalized city keys."""
    from models.db_models import CITY_TABLE_MAP

    for key in ("los angeles", "phoenix", "miami", "london"):
        assert key in CITY_TABLE_MAP, f"Missing key: {key}"


# -- standalone runner ----------------------------------------------------------

def _run(name: str, fn, db) -> None:
    print(f"\n=== {name} ===")
    try:
        fn(db)
        print("PASS")
    except Exception as exc:
        print(f"FAIL: {exc}")


if __name__ == "__main__":
    print("Running DB model tests...\n")
    from tests.test_conftest import TestSessionLocal, _engine
    from models.db_models import Base, CITY_TABLE_MAP
    from sqlalchemy import text

    Base.metadata.create_all(bind=_engine)
    session = TestSessionLocal()
    try:
        _run("test_user_table_exists", test_user_table_exists, session)
        _run("test_city_tables_exist", test_city_tables_exist, session)
        _run("test_user_insert_and_query", test_user_insert_and_query, session)
        _run("test_weather_insert_and_query", test_weather_insert_and_query, session)
        _run("test_city_table_map_keys", test_city_table_map_keys, session)
        session.rollback()
        # Remove any test rows that may exist from previous runs.
        for model in CITY_TABLE_MAP.values():
            session.execute(text(f"DELETE FROM {model.__tablename__}"))
        session.execute(text("DELETE FROM users WHERE username = 'testuser'"))
        session.commit()
    finally:
        session.close()
    print("\nDB model tests completed.")
