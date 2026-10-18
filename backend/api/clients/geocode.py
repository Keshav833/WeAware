
import httpx
from django.conf import settings


MAPBOX_GEOCODING_URL = (
    "https://api.mapbox.com/search/geocode/v6/forward"
)


class GeocodingError(Exception):
    """Raised when a location cannot be geocoded."""


def geocode_location(query: str) -> dict:
    """
    Convert a location query into geographic coordinates.

    Returns:
        {
            "name": str,
            "longitude": float,
            "latitude": float
        }
    """

    query = query.strip()

    if not query:
        raise ValueError("Location cannot be empty.")

    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise GeocodingError(
            "Mapbox access token is not configured."
        )

    try:
        response = httpx.get(
            MAPBOX_GEOCODING_URL,
            params={
                "q": query,
                "access_token": token,
                "limit": 1,
            },
            timeout=10.0,
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise GeocodingError(
            "Unable to contact the geocoding service."
        ) from exc

    data = response.json()
    features = data.get("features", [])

    if not features:
        raise GeocodingError(
            f"No location found for '{query}'."
        )

    feature = features[0]
    coordinates = feature["geometry"]["coordinates"]

    return {
        "name": feature.get("properties", {}).get(
            "full_address", query
        ),
        "longitude": coordinates[0],
        "latitude": coordinates[1],
    }
