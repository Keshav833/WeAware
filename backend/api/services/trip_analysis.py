from api.clients.geocode import geocode_location
from api.clients.routing import get_routes
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
        analyzed_routes.append(analysis)

    return {
        "origin": origin_location,
        "destination": destination_location,
        "routes": analyzed_routes,
        "route_count": len(analyzed_routes),
    }
