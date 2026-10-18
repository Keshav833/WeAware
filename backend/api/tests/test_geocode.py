
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings

from api.clients.geocode import (
    GeocodingError,
    geocode_location,
)


class GeocodingTests(SimpleTestCase):

    @override_settings(MAPBOX_ACCESS_TOKEN="")
    def test_missing_token(self):
        with self.assertRaises(GeocodingError):
            geocode_location("New York")

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            geocode_location("   ")

    @override_settings(MAPBOX_ACCESS_TOKEN="test-token")
    @patch("api.clients.geocode.httpx.get")
    def test_successful_geocoding(self, mock_get):
        mock_get.return_value = httpx.Response(
            200,
            json={
                "features": [
                    {
                        "geometry": {
                            "coordinates": [-74.006, 40.7128]
                        },
                        "properties": {
                            "full_address": "New York, NY, USA"
                        },
                    }
                ]
            },
            request=httpx.Request("GET", "https://example.com"),
        )

        result = geocode_location("New York")

        self.assertEqual(result["longitude"], -74.006)
        self.assertEqual(result["latitude"], 40.7128)
        self.assertEqual(result["name"], "New York, NY, USA")

    @override_settings(MAPBOX_ACCESS_TOKEN="test-token")
    @patch("api.clients.geocode.httpx.get")
    def test_no_results(self, mock_get):
        mock_get.return_value = httpx.Response(
            200,
            json={"features": []},
            request=httpx.Request("GET", "https://example.com"),
        )

        with self.assertRaises(GeocodingError):
            geocode_location("Unknown Place 123456")
