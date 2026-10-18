from datetime import datetime, timedelta

from api.clients.weather import get_weather_forecast
from api.services.weather_processing import normalize_weather_data


def fetch_checkpoint_weather(
    checkpoint: dict,
    forecast_hours: int = 48,
) -> list[dict]:
    """Fetch and normalize weather for a checkpoint around its ETA."""
    if forecast_hours < 1 or forecast_hours > 168:
        raise ValueError("forecast_hours must be between 1 and 168.")

    eta = checkpoint.get("eta")

    if isinstance(eta, str):
        eta = datetime.fromisoformat(eta.replace("Z", "+00:00"))

    if eta is None or not hasattr(eta, "tzinfo") or eta.tzinfo is None:
        raise ValueError("Checkpoint ETA must be timezone-aware.")

    start_date = eta.date().isoformat()
    end_date = (eta + timedelta(hours=forecast_hours)).date().isoformat()

    hourly = get_weather_forecast(
        latitude=checkpoint["latitude"],
        longitude=checkpoint["longitude"],
        start_date=start_date,
        end_date=end_date,
    )

    return normalize_weather_data(hourly)
