import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherError(Exception):
    """Raised when weather data cannot be retrieved or parsed."""


def get_weather_forecast(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Fetch hourly weather data for a location.

    Wind is returned in mph, precipitation in inches,
    and snowfall in centimeters by default unless configured.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "wind_speed_10m,"
            "rain,"
            "showers,"
            "snowfall"
        ),
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params=params,
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise WeatherError("Unable to retrieve weather forecast.") from exc
    except ValueError as exc:
        raise WeatherError("Weather provider returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise WeatherError("Weather provider returned an invalid response.")

    hourly = data.get("hourly")

    if not isinstance(hourly, dict):
        raise WeatherError("Weather response is missing hourly data.")

    required_fields = [
        "time",
        "wind_speed_10m",
        "rain",
        "showers",
        "snowfall",
    ]

    for field in required_fields:
        if field not in hourly:
            raise WeatherError(f"Weather response is missing {field}.")

    if any(not isinstance(hourly[field], list) for field in required_fields):
        raise WeatherError("Weather response contains invalid hourly data.")

    lengths = [len(hourly[field]) for field in required_fields]

    if len(set(lengths)) != 1:
        raise WeatherError("Weather response contains inconsistent hourly data.")

    return hourly