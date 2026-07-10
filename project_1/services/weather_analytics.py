"""Weather analytics queries — five hand-tuned raw SQL queries for performance,
plus two simple ORM lookups.

Every public method receives a SQLAlchemy ``Session`` so callers control
transaction boundaries.
"""

from datetime import date
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.api_models import (
    DayWeatherResponse,
    ExtremeDay,
    ExtremeHeatResponse,
    HottestDayResponse,
    MonthSummaryResponse,
    RainfallResponse,
    YearSummaryResponse,
)
from models.db_models import CITY_TABLE_MAP


def _resolve_table(city: str) -> str:
    """Return the physical table name for *city*, or raise ``ValueError``."""
    normalized = city.strip().lower()
    model = CITY_TABLE_MAP.get(normalized)
    if model is None:
        raise ValueError(f"Unsupported city: {city}")
    return model.__tablename__


# -- Simple ORM reads -----------------------------------------------------------

def get_day(db: Session, city: str, record_date: date) -> DayWeatherResponse:
    """Fetch a single day's weather record via ORM."""
    table = CITY_TABLE_MAP[city.strip().lower()]
    row = db.query(table).filter(table.date == record_date).first()
    if row is None:
        raise ValueError(f"No record found for {city} on {record_date}.")
    return DayWeatherResponse(
        city=city,
        date=row.date,
        temperature_2m_max=row.temperature_2m_max,
        temperature_2m_min=row.temperature_2m_min,
        temperature_2m_mean=row.temperature_2m_mean,
        precipitation_sum=row.precipitation_sum,
        wind_speed_10m_max=row.wind_speed_10m_max,
    )


def get_year_summary(db: Session, city: str, year: int) -> YearSummaryResponse:
    """Year-level aggregate summary via ORM (simple enough that ORM is fine)."""
    table = CITY_TABLE_MAP[city.strip().lower()]
    from sqlalchemy import func

    stmt = db.query(
        func.avg(table.temperature_2m_max).label("avg_max"),
        func.avg(table.temperature_2m_min).label("avg_min"),
        func.avg(table.temperature_2m_mean).label("avg_mean"),
        func.sum(table.precipitation_sum).label("total_precip"),
        func.avg(table.wind_speed_10m_max).label("avg_wind"),
        func.count(table.date).label("cnt"),
    ).filter(func.extract("year", table.date) == year)

    row = stmt.one()
    return YearSummaryResponse(
        city=city,
        year=year,
        avg_temp_max=row.avg_max,
        avg_temp_min=row.avg_min,
        avg_temp_mean=row.avg_mean,
        total_precipitation=row.total_precip,
        avg_wind_speed=row.avg_wind,
        record_count=row.cnt,
    )


# -- Hand-tuned raw SQL queries (5 queries) -------------------------------------

def get_month_summary(db: Session, city: str, year: int, month: int) -> MonthSummaryResponse:
    """Monthly aggregate summary — hand-tuned SQL for efficient AVG/SUM/COUNT in one scan."""
    tbl = _resolve_table(city)

    sql = text(f"""
        SELECT
            AVG(temperature_2m_max)   AS avg_max,
            AVG(temperature_2m_min)   AS avg_min,
            AVG(temperature_2m_mean)  AS avg_mean,
            SUM(precipitation_sum)    AS total_precip,
            AVG(wind_speed_10m_max)   AS avg_wind,
            COUNT(*)                  AS record_count
        FROM {tbl}
        WHERE EXTRACT(YEAR  FROM date) = :yr
          AND EXTRACT(MONTH FROM date) = :mo
    """)

    row = db.execute(sql, {"yr": year, "mo": month}).fetchone()
    return MonthSummaryResponse(
        city=city,
        year=year,
        month=month,
        avg_temp_max=row.avg_max,
        avg_temp_min=row.avg_min,
        avg_temp_mean=row.avg_mean,
        total_precipitation=row.total_precip,
        avg_wind_speed=row.avg_wind,
        record_count=row.record_count,
    )


def get_hottest_in_month(db: Session, city: str, year: int, month: int) -> HottestDayResponse:
    """Return the single hottest day in a given month — raw SQL with NULLS LAST."""
    tbl = _resolve_table(city)

    sql = text(f"""
        SELECT date, temperature_2m_max
        FROM {tbl}
        WHERE EXTRACT(YEAR  FROM date) = :yr
          AND EXTRACT(MONTH FROM date) = :mo
        ORDER BY temperature_2m_max DESC NULLS LAST
        LIMIT 1
    """)

    row = db.execute(sql, {"yr": year, "mo": month}).fetchone()
    if row is None:
        raise ValueError(f"No data for {city} in {year}-{month:02d}.")
    return HottestDayResponse(city=city, date=row.date, temperature_2m_max=row.temperature_2m_max)


def get_hottest_in_year(db: Session, city: str, year: int) -> HottestDayResponse:
    """Return the single hottest day in a given year — raw SQL with NULLS LAST."""
    tbl = _resolve_table(city)

    sql = text(f"""
        SELECT date, temperature_2m_max
        FROM {tbl}
        WHERE EXTRACT(YEAR FROM date) = :yr
        ORDER BY temperature_2m_max DESC NULLS LAST
        LIMIT 1
    """)

    row = db.execute(sql, {"yr": year}).fetchone()
    if row is None:
        raise ValueError(f"No data for {city} in {year}.")
    return HottestDayResponse(city=city, date=row.date, temperature_2m_max=row.temperature_2m_max)


def get_monthly_rainfall(db: Session, city: str, year: int, month: int) -> RainfallResponse:
    """Average daily precipitation for a month — raw SQL."""
    tbl = _resolve_table(city)

    sql = text(f"""
        SELECT AVG(precipitation_sum) AS avg_precip
        FROM {tbl}
        WHERE EXTRACT(YEAR  FROM date) = :yr
          AND EXTRACT(MONTH FROM date) = :mo
    """)

    row = db.execute(sql, {"yr": year, "mo": month}).fetchone()
    return RainfallResponse(
        city=city,
        year=year,
        month=month,
        avg_precipitation_mm=row.avg_precip,
    )


def get_extreme_heat_days(db: Session, city: str, year: int, month: int) -> ExtremeHeatResponse:
    """Count and list days where max temperature exceeded 32 °C (≈ 90 °F) — raw SQL."""
    tbl = _resolve_table(city)

    sql = text(f"""
        SELECT date, temperature_2m_max
        FROM {tbl}
        WHERE EXTRACT(YEAR  FROM date) = :yr
          AND EXTRACT(MONTH FROM date) = :mo
          AND temperature_2m_max > 32.0
        ORDER BY temperature_2m_max DESC
    """)

    rows = db.execute(sql, {"yr": year, "mo": month}).fetchall()
    extreme_days = [
        ExtremeDay(date=r.date, temperature_2m_max=r.temperature_2m_max)
        for r in rows
    ]
    return ExtremeHeatResponse(
        city=city,
        year=year,
        month=month,
        extreme_day_count=len(extreme_days),
        extreme_days=extreme_days,
    )
