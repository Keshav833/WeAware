from api.clients.weather import WeatherError
from api.services.checkpoint_weather import fetch_checkpoint_weather


def safe_fetch_checkpoint_weather(checkpoint: dict) -> dict:
    """Return a safe weather status instead of crashing on API failures."""
    try:
        records = fetch_checkpoint_weather(checkpoint)
        if not records:
            return {
                "available": False,
                "records": [],
                "reason": "Weather provider returned no forecast records.",
            }
        return {
            "available": True,
            "records": records,
            "reason": None,
        }
    except (WeatherError, ValueError) as exc:
        return {
            "available": False,
            "records": [],
            "reason": str(exc),
        }
