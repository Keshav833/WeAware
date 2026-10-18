
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
