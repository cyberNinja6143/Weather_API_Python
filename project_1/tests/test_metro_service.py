import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.metro import MetroWeatherService


def _assert_weather_response_for_city(city_name: str):
    service = MetroWeatherService()
    results = service.fetch_weather([city_name], date(2024, 1, 1), date(2024, 1, 2))

    print(f"Weather response for {city_name}:")
    for item in results:
        print(f"- City: {item.city}")
        print(f"  Date range: {item.start_date} to {item.end_date}")
        for record in item.records:
            print(
                f"  - {record.date}: temp={record.temperature_2m_max}, "
                f"precip={record.precipitation_sum}, wind={record.wind_speed_10m_max}"
            )

    assert len(results) == 1
    assert results[0].city == city_name
    assert results[0].records
    assert any(record.temperature_2m_max is not None for record in results[0].records)


def test_fetch_weather_returns_expected_records():
    _assert_weather_response_for_city("Phoenix")


def test_fetch_weather_returns_expected_records_for_los_angeles():
    _assert_weather_response_for_city("Los Angeles")


def test_fetch_weather_returns_expected_records_for_miami():
    _assert_weather_response_for_city("Miami")


def test_fetch_weather_returns_expected_records_for_london():
    _assert_weather_response_for_city("London")


def _run_test(name, test_func):
    print(f"\n=== {name} ===")
    try:
        test_func()
        print("PASS")
    except Exception as exc:
        print(f"FAIL: {exc}")


if __name__ == "__main__":
    print("Running metro service tests...\n")
    _run_test("test_fetch_weather_returns_expected_records", test_fetch_weather_returns_expected_records)
    _run_test("test_fetch_weather_returns_expected_records_for_los_angeles", test_fetch_weather_returns_expected_records_for_los_angeles)
    _run_test("test_fetch_weather_returns_expected_records_for_miami", test_fetch_weather_returns_expected_records_for_miami)
    _run_test("test_fetch_weather_returns_expected_records_for_london", test_fetch_weather_returns_expected_records_for_london)
    print("\nAll metro service tests completed.")
