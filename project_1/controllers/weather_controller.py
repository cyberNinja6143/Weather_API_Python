"""Controller for the /weather analytics endpoints.

Each function delegates to services/weather_analytics.py for data access
and returns a Pydantic response model for OpenAPI documentation.
"""

from datetime import date

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.api_models import (
    DayWeatherResponse,
    ExtremeHeatResponse,
    HottestDayResponse,
    MonthSummaryResponse,
    RainfallResponse,
    YearSummaryResponse,
)
from models.db_models import User
from services.auth import get_current_user
from services.db_session import get_db
from services.weather_analytics import (
    get_day,
    get_extreme_heat_days,
    get_hottest_in_month,
    get_hottest_in_year,
    get_month_summary,
    get_monthly_rainfall,
    get_year_summary,
)


def day_endpoint(
    city: str,
    record_date: date = Query(..., alias="date", description="Date in YYYY-MM-DD format."),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DayWeatherResponse:
    """Return the weather record for a single day in a city."""
    try:
        return get_day(db, city, record_date)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def month_summary_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> MonthSummaryResponse:
    """Return aggregated weather statistics for a calendar month."""
    try:
        return get_month_summary(db, city, year, month)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def year_summary_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> YearSummaryResponse:
    """Return aggregated weather statistics for a full year."""
    try:
        return get_year_summary(db, city, year)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def hottest_month_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> HottestDayResponse:
    """Return the hottest day in a given month."""
    try:
        return get_hottest_in_month(db, city, year, month)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def hottest_year_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> HottestDayResponse:
    """Return the hottest day in a given year."""
    try:
        return get_hottest_in_year(db, city, year)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def rainfall_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RainfallResponse:
    """Return the average daily rainfall for a month."""
    try:
        return get_monthly_rainfall(db, city, year, month)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def extreme_heat_endpoint(
    city: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ExtremeHeatResponse:
    """Return the count and list of extreme-heat days (>32°C) in a month."""
    try:
        return get_extreme_heat_days(db, city, year, month)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
