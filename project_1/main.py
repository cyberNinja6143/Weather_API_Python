"""Weather Analytics API entrypoint.

Start with: uvicorn main:app --reload
"""

from fastapi import FastAPI

from routes.auth_routes import router as auth_router
from routes.ingestion_routes import router as ingestion_router
from routes.weather_routes import router as weather_router
from services.db_session import init_db

app = FastAPI(
    title="Weather Analytics API",
    version="1.0.0",
    description="Query daily weather records for Los Angeles, Phoenix, Miami, and London.",
)

app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(ingestion_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
