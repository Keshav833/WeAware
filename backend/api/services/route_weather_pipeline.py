from api.services.checkpoint_analysis import analyze_checkpoint
from api.services.route_analysis import build_route_checkpoints
from api.services.route_summary import summarize_route
from api.services.safe_weather import safe_fetch_checkpoint_weather


def analyze_route_with_weather(
    route: dict,
    departure_utc,
    load_lb: float,
    interval_miles: int = 25,
) -> dict:
    """Generate checkpoints, fetch weather for each, and summarize risk."""
    if load_lb <= 0:
        raise ValueError("Load weight must be positive.")

    route_data = build_route_checkpoints(
        route=route,
        departure_utc=departure_utc,
        interval_miles=interval_miles,
    )

    analyzed_checkpoints = []

    for checkpoint in route_data["checkpoints"]:
        weather_result = safe_fetch_checkpoint_weather(checkpoint)
        analyzed = analyze_checkpoint(
            checkpoint=checkpoint,
            weather_records=weather_result["records"],
            load_lb=load_lb,
        )

        if not weather_result["available"]:
            analyzed["weather_available"] = False
            analyzed["risk_level"] = None
            analyzed["risk_label"] = "Unknown"
            analyzed["weather_reason"] = weather_result["reason"]

        analyzed_checkpoints.append(analyzed)

    summary = summarize_route(analyzed_checkpoints)

    return {
        "route_id": route_data["route_id"],
        "distance_miles": route_data["route_distance_miles"],
        "duration_seconds": route_data["duration_seconds"],
        "checkpoints": analyzed_checkpoints,
        "summary": summary,
    }
