from api.clients.geocode import geocode_location
from api.clients.routing import get_routes
from api.services.route_comparison import score_route
from api.services.route_ranking import rank_scored_routes
from api.services.route_weather_pipeline import analyze_route_with_weather


def analyze_trip(
    origin: str,
    destination: str,
    departure_utc,
    load_lb: float,
    interval_miles: int = 25,
) -> dict:
    """Geocode locations, fetch routes, and analyze each route's weather risk."""
    origin_location = geocode_location(origin)
    destination_location = geocode_location(destination)
    routes = get_routes(origin_location, destination_location)

    analyzed_routes = []

    for route in routes:
        analysis = analyze_route_with_weather(
            route=route,
            departure_utc=departure_utc,
            load_lb=load_lb,
            interval_miles=interval_miles,
        )
        analysis["route_id"] = route.get("id")
        analysis["geometry"] = route.get("geometry")
        comparison = score_route(analysis)
        analysis["comparison"] = comparison
        analysis["scoring_available"] = comparison["scoring_available"]

        if comparison["scoring_available"]:
            analysis["score"] = comparison["score"]
        else:
            analysis["score"] = None
            analysis["scoring_reason"] = comparison["scoring_reason"]

        analyzed_routes.append(analysis)

    ranked = rank_scored_routes(analyzed_routes)
    rank_by_id = {
        route["route_id"]: route["rank"]
        for route in ranked
    }

    for route in analyzed_routes:
        route["rank"] = rank_by_id.get(route["route_id"])
        route["recommended"] = (
            route["route_id"] in rank_by_id
            and rank_by_id[route["route_id"]] == 1
        )

    recommendation = next(
        (
            route["route_id"]
            for route in analyzed_routes
            if route["recommended"]
        ),
        None,
    )

    return {
        "origin": origin_location,
        "destination": destination_location,
        "routes": analyzed_routes,
        "route_count": len(analyzed_routes),
        "recommendation_route_id": recommendation,
        "recommendation_note": (
            "Risk miles are estimates based on midpoint-assigned "
            "checkpoint segments."
        ),
    }
