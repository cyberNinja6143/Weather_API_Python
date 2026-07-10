"""Ingestion pipeline: fetch Open-Meteo → pandas clean → PostgreSQL insert.

Also provides purge and test-data detection.  Every public function receives a
SQLAlchemy ``Session`` so callers control transaction boundaries.
"""

import logging
import os
from datetime import date
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.db_models import CITY_TABLE_MAP
from services.city_coordinates import CityCoordinates

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger(__name__)

METEO_URL = os.getenv("OPEN_METEO_ARCHIVE_URL")
INGEST_YEAR = 2025
INGEST_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
]


# -- Population check -----------------------------------------------------------

def is_any_city_populated(db: Session, cities: List[str]) -> bool:
    """Return True if *any* city table already contains rows for the ingest year."""
    for city in cities:
        tbl = _resolve_table(city)
        count = db.execute(
            text(f"SELECT COUNT(*) FROM {tbl} WHERE EXTRACT(YEAR FROM date) = :yr"),
            {"yr": INGEST_YEAR},
        ).scalar()
        if count and count > 0:
            return True
    return False


# -- Fetch + clean per city -----------------------------------------------------

def _fetch_raw(city: str) -> dict:
    """Call Open-Meteo for a full year and return the JSON payload."""
    lat = CityCoordinates.latitude(city)
    lon = CityCoordinates.longitude(city)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date(INGEST_YEAR, 1, 1).isoformat(),
        "end_date": date(INGEST_YEAR, 12, 31).isoformat(),
        "daily": ",".join(INGEST_VARIABLES),
        "timezone": "auto",
    }
    resp = requests.get(METEO_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _clean_with_pandas(raw: dict, city: str) -> pd.DataFrame:
    """Flatten the Open-Meteo JSON, drop fully-null rows, and validate value ranges."""
    daily = raw.get("daily", {})
    dates = daily.get("time", [])

    if not dates:
        raise ValueError(f"No daily data returned for {city}.")

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(dates).date,
            "temperature_2m_max": daily.get("temperature_2m_max"),
            "temperature_2m_min": daily.get("temperature_2m_min"),
            "temperature_2m_mean": daily.get("temperature_2m_mean"),
            "precipitation_sum": daily.get("precipitation_sum"),
            "wind_speed_10m_max": daily.get("wind_speed_10m_max"),
        }
    )

    # Drop rows where every measurement column is null.
    measure_cols = [c for c in df.columns if c != "date"]
    before = len(df)
    df = df.dropna(subset=measure_cols, how="all")
    if before != len(df):
        logger.info("%s: dropped %d fully-null rows.", city, before - len(df))

    # Replace remaining NaN with None so they become SQL NULL.
    df = df.where(pd.notnull(df), None)

    # Clamp out-of-range values to None per column.
    _clamp(df, "temperature_2m_max", -80, 60, city)
    _clamp(df, "temperature_2m_min", -80, 60, city)
    _clamp(df, "temperature_2m_mean", -80, 60, city)
    _clamp(df, "precipitation_sum", 0, 500, city)
    _clamp(df, "wind_speed_10m_max", 0, 400, city)

    return df


def _clamp(df: pd.DataFrame, col: str, lo: float, hi: float, city: str) -> None:
    """Set values in *col* that fall outside [lo, hi] to None."""
    mask = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
    if mask.any():
        logger.warning("%s: %d out-of-range values in %s → set to None.", city, mask.sum(), col)
        df.loc[mask, col] = None


# -- Insert ---------------------------------------------------------------------

def _insert_city_data(db: Session, city: str, df: pd.DataFrame) -> int:
    """Upsert every row in the DataFrame into the matching city table."""
    tbl = _resolve_table(city)
    written = 0
    for _, row in df.iterrows():
        db.execute(
            text(
                f"INSERT INTO {tbl} "
                f"(date, temperature_2m_max, temperature_2m_min, temperature_2m_mean, "
                f"precipitation_sum, wind_speed_10m_max) "
                f"VALUES (:d, :tmax, :tmin, :tmean, :precip, :wind) "
                f"ON CONFLICT (date) DO UPDATE SET "
                f"  temperature_2m_max = EXCLUDED.temperature_2m_max,"
                f"  temperature_2m_min  = EXCLUDED.temperature_2m_min,"
                f"  temperature_2m_mean = EXCLUDED.temperature_2m_mean,"
                f"  precipitation_sum   = EXCLUDED.precipitation_sum,"
                f"  wind_speed_10m_max  = EXCLUDED.wind_speed_10m_max"
            ),
            {
                "d": row["date"],
                "tmax": _none_if_pdna(row.get("temperature_2m_max")),
                "tmin": _none_if_pdna(row.get("temperature_2m_min")),
                "tmean": _none_if_pdna(row.get("temperature_2m_mean")),
                "precip": _none_if_pdna(row.get("precipitation_sum")),
                "wind": _none_if_pdna(row.get("wind_speed_10m_max")),
            },
        )
        written += 1
    db.flush()
    return written


# -- Public API -----------------------------------------------------------------

def ingest_all_cities(db: Session, cities: List[str]) -> Dict:
    """Full pipeline for every city: check → fetch → clean → insert.

    Returns a summary dict.  If all tables already contain {INGEST_YEAR} data,
    returns immediately with ``"status": "already_populated"``.
    """
    if is_any_city_populated(db, cities):
        return {"status": "already_populated", "message": f"All city tables already contain {INGEST_YEAR} data."}

    start = date(INGEST_YEAR, 1, 1)
    end = date(INGEST_YEAR, 12, 31)
    summary: Dict[str, dict] = {}

    for city in cities:
        raw = _fetch_raw(city)
        df = _clean_with_pandas(raw, city)
        count = _insert_city_data(db, city, df)
        summary[city] = {"rows_inserted": count, "date_range": f"{start} → {end}"}

    db.commit()
    return {"status": "ingested", "cities": summary}


def truncate_weather_tables(db: Session) -> Dict:
    """TRUNCATE every city weather table.  The users table is never touched."""
    cleared: List[str] = []
    for model in CITY_TABLE_MAP.values():
        tbl = model.__tablename__
        db.execute(text(f"TRUNCATE TABLE {tbl}"))
        cleared.append(tbl)
    db.commit()
    return {"status": "purged", "tables_cleared": cleared}


def remove_non_2025_data(db: Session) -> Dict:
    """Delete any row in weather tables whose date year is not {INGEST_YEAR}.

    Useful for cleaning up test/junk data before a fresh ingest.
    """
    removed: Dict[str, int] = {}
    for model in CITY_TABLE_MAP.values():
        tbl = model.__tablename__
        result = db.execute(
            text(f"DELETE FROM {tbl} WHERE EXTRACT(YEAR FROM date) != :yr"),
            {"yr": INGEST_YEAR},
        )
        removed[tbl] = result.rowcount
    db.commit()
    return {"status": "cleaned", "rows_removed": removed}


# -- Helpers --------------------------------------------------------------------

def _resolve_table(city: str) -> str:
    normalized = city.strip().lower()
    model = CITY_TABLE_MAP.get(normalized)
    if model is None:
        raise ValueError(f"Unsupported city: {city}")
    return model.__tablename__


def _none_if_pdna(value):
    """Return None if *value* is pandas NA/NaN, otherwise the value itself."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value
