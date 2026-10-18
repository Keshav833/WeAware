
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings

from api.clients.routing import RoutingError, get_routes


class RoutingTests(SimpleTestCase):

    def setUp(self):
        self.origin = {
            "longitude": -74.006,
            "latitude": 40.7128,
        }
        self.destination = {
            "longitude": -71.0589,
            "latitude": 42.3601,
        }

    @override_settings(MAPBOX_ACCESS_TOKEN="")
    def test_missing_token(self):
        with self.assertRaises(RoutingError):
            get_routes(self.origin, self.destination)

    @override_settings(MAPBOX_ACCESS_TOKEN="test-token")
    @patch("api.clients.routing.httpx.get")
    def test_successful_route(self, mock_get):
        mock_get.return_value = httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [
                    {
                        "distance": 160934.4,
                        "duration": 7200,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [-74.006, 40.7128],
                                [-71.0589, 42.3601],
                            ],
                        },
                        "legs": [],
                    }
                ],
            },
            request=httpx.Request(
                "GET", "https://example.com"
            ),
        )

        routes = get_routes(
            self.origin, self.destination
        )

        self.assertEqual(len(routes), 1)
        self.assertAlmostEqual(
            routes[0]["distance_miles"], 100
        )
        self.assertEqual(
            routes[0]["duration_seconds"], 7200
        )
        self.assertEqual(routes[0]["id"], 1)

    @override_settings(MAPBOX_ACCESS_TOKEN="test-token")
    @patch("api.clients.routing.httpx.get")
    def test_no_routes_found(self, mock_get):
        mock_get.return_value = httpx.Response(
            200,
            json={"code": "NoRoute", "routes": []},
            request=httpx.Request(
                "GET", "https://example.com"
            ),
        )

        with self.assertRaises(RoutingError):
            get_routes(self.origin, self.destination)


def parse_route_geometry(route: dict) -> dict:
    """
    Extract route coordinates and segment distances from a Mapbox route.

    Mapbox coordinates use [longitude, latitude].
    Our backend uses (latitude, longitude).
    """
    geometry = route.get("geometry", {})
    raw_coordinates = geometry.get("coordinates", [])

    if len(raw_coordinates) < 2:
        raise ValueError("Route must contain at least two coordinates.")

    coordinates = []

    for point in raw_coordinates:
        if len(point) < 2:
            raise ValueError("Invalid coordinate in route geometry.")

        longitude, latitude = point[0], point[1]

        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude is out of range.")

        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude is out of range.")

        coordinates.append((latitude, longitude))

    segment_distances = []

    for index in range(len(coordinates) - 1):
        start = coordinates[index]
        end = coordinates[index + 1]

        distance = haversine_miles(
            start[0],
            start[1],
            end[0],
            end[1],
        )

        segment_distances.append(distance)

    return {
        "coordinates": coordinates,
        "segment_distances_miles": segment_distances,
        "total_geometry_miles": sum(segment_distances),
        "route_distance_miles": route.get("distance_miles"),
        "duration_seconds": route.get("duration_seconds"),
    }