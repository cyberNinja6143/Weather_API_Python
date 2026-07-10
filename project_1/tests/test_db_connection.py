import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.db_connection import connect_to_weather_db


def smoke_test_connection():
    """Attempt a real connection and report whether the database is reachable."""
    try:
        connection = connect_to_weather_db()
        connection.close()
        print("Connection successful.")
    except Exception as exc:
        print(f"Connection failed: {exc}")


if __name__ == "__main__":
    smoke_test_connection()
