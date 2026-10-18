from datetime import datetime, timezone


def match_weather_to_checkpoint(
    checkpoint: dict,
    weather_records: list[dict],
) -> dict:
    """
    Find the hourly weather record corresponding to a checkpoint ETA.

    checkpoint must contain an aware datetime under "eta".
    weather_records come from normalize_weather_data().
    """
    eta = checkpoint.get("eta")

    if isinstance(eta, str):
        eta = datetime.fromisoformat(eta.replace("Z", "+00:00"))

    if not isinstance(eta, datetime) or eta.tzinfo is None:
        raise ValueError("Checkpoint ETA must be a timezone-aware datetime.")

    eta = eta.astimezone(timezone.utc)

    matching_record = None

    for record in weather_records:
        record_time = record.get("time")

        if not isinstance(record_time, datetime) or record_time.tzinfo is None:
            continue

        record_time = record_time.astimezone(timezone.utc)

        if record_time <= eta:
            if (
                matching_record is None
                or record_time > matching_record["time"]
            ):
                matching_record = {
                    **record,
                    "time": record_time,
                }

    if matching_record is None:
        return {
            "available": False,
            "reason": "No forecast record exists at or before checkpoint ETA.",
        }

    # Do not use stale weather from hours earlier.
    age_seconds = (eta - matching_record["time"]).total_seconds()

    if age_seconds >= 3600:
        return {
            "available": False,
            "reason": "No forecast record is available for the checkpoint hour.",
        }

    if not matching_record.get("available", False):
        return {
            "available": False,
            "reason": "Weather measurements are incomplete.",
        }

    return {
        "available": True,
        "checkpoint_eta": eta.isoformat(),
        "weather_time": matching_record["time"].isoformat(),
        "wind_mph": matching_record["wind_mph"],
        "rain_inches": matching_record["rain_inches"],
        "snow_inches": matching_record["snow_inches"],
    }