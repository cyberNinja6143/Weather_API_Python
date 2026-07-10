"""Routes under /weather — all JWT-protected analytics endpoints."""

from fastapi import Depends, APIRouter

from controllers.weather_controller import (
    day_endpoint,
    extreme_heat_endpoint,
    hottest_month_endpoint,
    hottest_year_endpoint,
    month_summary_endpoint,
    rainfall_endpoint,
    year_summary_endpoint,
)
from services.auth import get_current_user

router = APIRouter(
    prefix="/weather",
    tags=["Weather Analytics"],
    dependencies=[Depends(get_current_user)],
)

router.add_api_route("/{city}/day", day_endpoint, methods=["GET"])
router.add_api_route("/{city}/month", month_summary_endpoint, methods=["GET"])
router.add_api_route("/{city}/year", year_summary_endpoint, methods=["GET"])
router.add_api_route("/{city}/hottest/month", hottest_month_endpoint, methods=["GET"])
router.add_api_route("/{city}/hottest/year", hottest_year_endpoint, methods=["GET"])
router.add_api_route("/{city}/rainfall", rainfall_endpoint, methods=["GET"])
router.add_api_route("/{city}/extreme-heat", extreme_heat_endpoint, methods=["GET"])
