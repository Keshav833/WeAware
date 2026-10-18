
import httpx
from django.conf import settings


MAPBOX_DIRECTIONS_URL = (
    "https://api.mapbox.com/directions/v5/mapbox/driving"
)


class RoutingError(Exception):
    """Raised when route generation fails."""


def get_routes(
    origin: dict,
    destination: dict,
) -> list[dict]:
    """
    Retrieve driving routes from Mapbox.

    Coordinates are passed as longitude,latitude.
    """

    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise RoutingError(
            "Mapbox access token is not configured."
        )

    origin_coords = (
        f"{origin['longitude']},{origin['latitude']}"
    )
    destination_coords = (
        f"{destination['longitude']},{destination['latitude']}"
    )

    url = (
        f"{MAPBOX_DIRECTIONS_URL}/"
        f"{origin_coords};{destination_coords}"
    )

    try:
        response = httpx.get(
            url,
            params={
                "access_token": token,
                "alternatives": "true",
                "geometries": "geojson",
                "overview": "full",
                "steps": "false",
                "annotations": "distance,duration",
            },
            timeout=20.0,
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise RoutingError(
            "Unable to retrieve driving routes."
        ) from exc

    data = response.json()

    if data.get("code") != "Ok":
        raise RoutingError(
            data.get("message", "Route generation failed.")
        )

    routes = data.get("routes", [])

    if not routes:
        raise RoutingError("No driving routes were found.")

    return [
        {
            "id": index + 1,
            "distance_miles": route["distance"] / 1609.344,
            "duration_seconds": route["duration"],
            "geometry": route["geometry"],
            "legs": route["legs"],
        }
        for index, route in enumerate(routes)
    ]
