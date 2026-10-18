from api.services.route_scoring import calculate_route_score
from api.services.route_segments import build_risk_segments


def score_route(route: dict) -> dict:
    distance = route.get("distance_miles")
    duration = route.get("duration_seconds")

    if distance is None or duration is None:
        raise ValueError("Route distance and duration are required.")

    segments = build_risk_segments(
        route.get("checkpoints", []),
        distance,
    )

    if any(segment["risk_level"] is None for segment in segments):
        return {
            "route_id": route.get("route_id"),
            "scoring_available": False,
            "scoring_reason": "Weather risk is incomplete.",
            "risk_segments": segments,
        }

    score = calculate_route_score(
        risk_segments=segments,
        total_distance_miles=distance,
        duration_seconds=duration,
    )

    return {
        "route_id": route.get("route_id"),
        "scoring_available": True,
        "scoring_reason": None,
        "risk_segments": segments,
        "score": score,
    }
