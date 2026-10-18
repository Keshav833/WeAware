from api.services.route_analysis import build_route_checkpoints
from api.services.checkpoint_analysis import analyze_checkpoint
from api.services.route_summary import summarize_route


def analyze_route(
    route: dict,
    departure_utc,
    weather_by_checkpoint: list[list[dict]],
    load_lb: float,
    interval_miles: int = 25,
) -> dict:
    """
    Analyze checkpoints and summarize risk for one route.

    weather_by_checkpoint[i] contains the hourly weather records
    available for checkpoint i.
    """
    route_checkpoints = build_route_checkpoints(
        route=route,
        departure_utc=departure_utc,
        interval_miles=interval_miles,
    )

    checkpoints = route_checkpoints["checkpoints"]

    if len(weather_by_checkpoint) != len(checkpoints):
        raise ValueError(
            "Weather data must be provided for every checkpoint."
        )

    analyzed_checkpoints = []

    for checkpoint, weather_records in zip(
        checkpoints,
        weather_by_checkpoint,
    ):
        analyzed = analyze_checkpoint(
            checkpoint=checkpoint,
            weather_records=weather_records,
            load_lb=load_lb,
        )
        analyzed_checkpoints.append(analyzed)

    summary = summarize_route(analyzed_checkpoints)

    return {
        "route_id": route_checkpoints["route_id"],
        "distance_miles": route_checkpoints["route_distance_miles"],
        "duration_seconds": route_checkpoints["duration_seconds"],
        "checkpoints": analyzed_checkpoints,
        "summary": summary,
    }