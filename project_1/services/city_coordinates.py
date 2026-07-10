class CityCoordinates:
    @staticmethod
    def latitude(city: str) -> float:
        coordinates = {
            "phoenix": 33.4484,
            "los angeles": 34.0522,
            "miami florida": 25.7617,
            "london": 51.5074,
        }
        normalized = city.strip().lower()
        if normalized not in coordinates:
            raise ValueError(f"Unsupported city: {city}")
        return coordinates[normalized]

    @staticmethod
    def longitude(city: str) -> float:
        coordinates = {
            "phoenix": -112.0740,
            "los angeles": -118.2437,
            "miami florida": -80.1918,
            "london": -0.1278,
        }
        normalized = city.strip().lower()
        if normalized not in coordinates:
            raise ValueError(f"Unsupported city: {city}")
        return coordinates[normalized]
