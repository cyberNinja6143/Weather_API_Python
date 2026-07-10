"""Controller for /admin endpoints — ingestion and purge, JWT-protected.

Uses a module-level lock + state machine to prevent concurrent ingestion runs.
"""

import threading
from enum import Enum
from http import HTTPStatus

from fastapi import Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from models.db_models import User
from services.auth import get_current_user
from services.db_session import SessionLocal, get_db
from services.weather_ingestion import (
    INGEST_YEAR,
    ingest_all_cities,
    is_any_city_populated,
    remove_non_2025_data,
    truncate_weather_tables,
)

CITIES = ["los angeles", "phoenix", "miami", "london"]


class _IngestState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    POPULATED = "populated"


_state = _IngestState.IDLE
_lock = threading.Lock()


def _run_ingestion() -> None:
    """Background worker: clean test data, fetch, clean, insert, update state."""
    global _state
    db = SessionLocal()
    try:
        remove_non_2025_data(db)
        ingest_all_cities(db, CITIES)
        with _lock:
            _state = _IngestState.POPULATED
    except Exception:
        with _lock:
            _state = _IngestState.IDLE
        raise
    finally:
        db.close()


def ingest_endpoint(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    """Start or check the weather-data ingestion for {INGEST_YEAR}.

    * **200 OK** — data is already present (or just finished).
    * **202 Accepted** — ingestion has been started (first request).
    * **409 Conflict** — another ingestion is already in progress.
    """
    global _state
    with _lock:
        if _state == _IngestState.POPULATED:
            return Response(status_code=HTTPStatus.OK, content='{"status":"already_populated"}')
        if _state == _IngestState.PROCESSING:
            return Response(
                status_code=HTTPStatus.CONFLICT,
                content='{"status":"processing","detail":"An ingestion is already in progress."}',
            )
        # Also return 200 if rows exist but state is IDLE (e.g. after a server restart).
        if is_any_city_populated(db, CITIES):
            _state = _IngestState.POPULATED
            return Response(status_code=HTTPStatus.OK, content='{"status":"already_populated"}')
        # Not populated and not processing — start the background job.
        _state = _IngestState.PROCESSING

    thread = threading.Thread(target=_run_ingestion, daemon=True)
    thread.start()
    return Response(
        status_code=HTTPStatus.ACCEPTED,
        content='{"status":"ingestion_started","year":%d}' % INGEST_YEAR,
    )


def purge_endpoint(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Truncate all city weather tables.  The users table is never affected.

    Resets the ingestion state so a subsequent ``POST /admin/ingest`` will
    re-fetch data.
    """
    global _state
    try:
        result = truncate_weather_tables(db)
        with _lock:
            _state = _IngestState.IDLE
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Purge failed: {exc}") from exc
