import math
from datetime import datetime, timezone


CM_TO_INCHES = 1 / 2.54


def normalize_weather_data(hourly: dict) -> list[dict]:
    """
    Convert Open-Meteo hourly data into normalized records.

    Wind: mph
    Rain: inches per hour (hourly precipitation amount)
    Snow: inches per hour (hourly snowfall amount)
    Time: timezone-aware UTC datetime
    """
    required_fields = [
        "time",
        "wind_speed_10m",
        "rain",
        "showers",
        "snowfall",
    ]

    for field in required_fields:
        if field not in hourly:
            raise ValueError(f"Missing weather field: {field}")

    lengths = [len(hourly[field]) for field in required_fields]

    if len(set(lengths)) != 1:
        raise ValueError("Weather fields have inconsistent lengths.")

    records = []

    for index, time_value in enumerate(hourly["time"]):
        wind = hourly["wind_speed_10m"][index]
        rain = hourly["rain"][index]
        showers = hourly["showers"][index]
        snowfall_cm = hourly["snowfall"][index]

        values = [wind, rain, showers, snowfall_cm]

        if not isinstance(time_value, str):
            raise ValueError("Weather timestamps must be strings.")

        if any(value is None for value in values):
            records.append({
                "time": _parse_utc_time(time_value),
                "wind_mph": None,
                "rain_inches": None,
                "snow_inches": None,
                "available": False,
            })
            continue

        if any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in values
        ):
            raise ValueError("Weather measurements must be finite numbers.")

        if any(value < 0 for value in values):
            raise ValueError("Weather measurements cannot be negative.")

        records.append({
            "time": _parse_utc_time(time_value),
            "wind_mph": float(wind),
            "rain_inches": float(rain) + float(showers),
            "snow_inches": float(snowfall_cm) * CM_TO_INCHES,
            "available": True,
        })

    return records


def _parse_utc_time(value: str) -> datetime:
    """Parse an ISO timestamp and ensure it is timezone-aware UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)