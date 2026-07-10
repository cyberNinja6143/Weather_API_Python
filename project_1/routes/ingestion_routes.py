"""Routes under /admin — ingestion and weather-table purge, JWT-protected."""

from fastapi import Depends, APIRouter

from controllers.ingestion_controller import ingest_endpoint, purge_endpoint
from services.auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_user)],
)

router.add_api_route("/ingest", ingest_endpoint, methods=["POST"])
router.add_api_route("/purge-weather", purge_endpoint, methods=["POST"])
