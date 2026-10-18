from datetime import datetime

from api.services.geometry import (
    generate_checkpoints,
    parse_route_geometry,
)


def build_route_checkpoints(
    route: dict,
    departure_utc: datetime,
    interval_miles: int = 25,
) -> dict:
    """
    Prepare checkpoint locations and estimated arrival times
    for one Mapbox route.
    """
    parsed_route = parse_route_geometry(route)

    checkpoints = generate_checkpoints(
        coordinates=parsed_route["coordinates"],
        departure=departure_utc,
        total_duration_seconds=parsed_route["duration_seconds"],
        interval_miles=interval_miles,
    )

    return {
        "route_id": route.get("id"),
        "route_distance_miles": parsed_route["route_distance_miles"],
        "duration_seconds": parsed_route["duration_seconds"],
        "checkpoints": [
            {
                "distance_miles": checkpoint.distance_miles,
                "latitude": checkpoint.latitude,
                "longitude": checkpoint.longitude,
                "eta": checkpoint.eta.isoformat(),
            }
            for checkpoint in checkpoints
        ],
    }