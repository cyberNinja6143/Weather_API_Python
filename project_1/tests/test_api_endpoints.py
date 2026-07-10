"""End-to-end API tests using FastAPI TestClient.

Run standalone:  python tests/test_api_endpoints.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date

from tests.test_conftest import test_client, seeded_weather_data  # noqa: F401


def _register_user(client) -> None:
    """Helper: directly insert a test user so login tests can succeed."""
    # Use the overridden DB dependency to insert a user row.
    from models.db_models import User
    from services.auth import hash_password
    from services.db_session import get_db

    db = next(get_db())
    try:
        existing = db.query(User).filter(User.username == "tester").first()
        if existing is None:
            db.add(User(username="tester", password_hash=hash_password("pass123")))
            db.commit()
    finally:
        db.close()


def test_login_valid_credentials(test_client) -> None:  # noqa: F811
    """POST /auth/login with correct credentials returns a token."""
    _register_user(test_client)
    resp = test_client.post("/auth/login", json={"username": "tester", "password": "pass123"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_invalid_credentials(test_client) -> None:  # noqa: F811
    """POST /auth/login with a wrong password returns 401."""
    _register_user(test_client)
    resp = test_client.post("/auth/login", json={"username": "tester", "password": "WRONG"})
    assert resp.status_code == 401


def test_weather_endpoint_requires_auth(test_client) -> None:  # noqa: F811
    """GET /weather/phoenix/day without a token returns 401 or 403."""
    resp = test_client.get("/weather/phoenix/day", params={"date": "2025-06-01"})
    assert resp.status_code in (401, 403)


def test_weather_day_with_valid_token(test_client, seeded_weather_data) -> None:  # noqa: F811
    """Login, then use the token to query a day endpoint."""
    _register_user(test_client)
    login_resp = test_client.post("/auth/login", json={"username": "tester", "password": "pass123"})
    token = login_resp.json()["access_token"]

    resp = test_client.get(
        "/weather/phoenix/day",
        params={"date": "2025-06-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["city"] == "phoenix"
    assert body["date"] == "2025-06-01"


def test_swagger_docs_accessible(test_client) -> None:  # noqa: F811
    """GET /docs returns 200."""
    resp = test_client.get("/docs")
    assert resp.status_code == 200


def test_openapi_json_contains_paths(test_client) -> None:  # noqa: F811
    """GET /openapi.json returns a valid spec with expected paths."""
    resp = test_client.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.json()
    paths = body.get("paths", {})
    assert "/auth/login" in paths
    assert "/weather/{city}/day" in paths
    assert "/weather/{city}/extreme-heat" in paths


# -- standalone runner ----------------------------------------------------------

def _run(name: str, fn, *args) -> None:
    print(f"\n=== {name} ===")
    try:
        fn(*args)
        print("PASS")
    except Exception as exc:
        print(f"FAIL: {exc}")


if __name__ == "__main__":
    print("Running API endpoint tests...\n")
    from tests.test_conftest import TestSessionLocal, _engine, CITIES, _insert_weather_rows
    from models.db_models import Base, User, CITY_TABLE_MAP
    from services.auth import hash_password
    from services.db_session import get_db
    from main import app
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    Base.metadata.create_all(bind=_engine)

    db = TestSessionLocal()
    try:
        for city in CITIES:
            _insert_weather_rows(db, city, date(2025, 6, 1), rows=5)
        existing = db.query(User).filter(User.username == "tester").first()
        if existing is None:
            db.add(User(username="tester", password_hash=hash_password("pass123")))
        db.commit()
    finally:
        db.close()

    def _override_db():
        sess = TestSessionLocal()
        try:
            yield sess
        finally:
            sess.close()

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    try:
        _run("test_login_valid_credentials", test_login_valid_credentials, client)
        _run("test_login_invalid_credentials", test_login_invalid_credentials, client)
        _run("test_weather_endpoint_requires_auth", test_weather_endpoint_requires_auth, client)
        _run("test_weather_day_with_valid_token", test_weather_day_with_valid_token, client, None)
        _run("test_swagger_docs_accessible", test_swagger_docs_accessible, client)
        _run("test_openapi_json_contains_paths", test_openapi_json_contains_paths, client)
    finally:
        app.dependency_overrides.clear()

    # Remove all test data committed above.
    cleanup = TestSessionLocal()
    try:
        for model in CITY_TABLE_MAP.values():
            cleanup.execute(text(f"DELETE FROM {model.__tablename__}"))
        cleanup.execute(text("DELETE FROM users WHERE username = 'tester'"))
        cleanup.commit()
    finally:
        cleanup.close()

    print("\nAPI endpoint tests completed.")
