from api.services.risk import checkpoint_risk, RiskLevel
from api.services.weather_matching import match_weather_to_checkpoint


RISK_LABELS = {
    RiskLevel.LOW: "Low",
    RiskLevel.MODERATE: "Moderate",
    RiskLevel.HIGH: "High",
    RiskLevel.SEVERE: "Severe",
    RiskLevel.NO_TRAVEL: "No Travel",
}


def analyze_checkpoint(
    checkpoint: dict,
    weather_records: list[dict],
    load_lb: float,
) -> dict:
    """
    Match weather to the checkpoint ETA and calculate risk.
    """
    weather = match_weather_to_checkpoint(
        checkpoint,
        weather_records,
    )

    result = {
        "distance_miles": checkpoint.get("distance_miles"),
        "latitude": checkpoint.get("latitude"),
        "longitude": checkpoint.get("longitude"),
        "eta": (
            checkpoint["eta"].isoformat()
            if hasattr(checkpoint.get("eta"), "isoformat")
            else checkpoint.get("eta")
        ),
    }

    if not weather["available"]:
        return {
            **result,
            "risk_level": None,
            "risk_label": "Unknown",
            "weather_available": False,
            "weather_reason": weather.get("reason"),
        }

    risk = checkpoint_risk(
        wind_mph=weather["wind_mph"],
        rain_inches_per_hour=weather["rain_inches"],
        snow_inches_per_hour=weather["snow_inches"],
        load_lb=load_lb,
    )

    return {
        **result,
        "risk_level": int(risk),
        "risk_label": RISK_LABELS[risk],
        "weather_available": True,
        "weather": weather,
    }