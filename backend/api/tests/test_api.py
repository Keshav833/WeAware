from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient

from api.clients.geocode import GeocodingError
from api.clients.routing import RoutingError


class AnalysisApiTests(SimpleTestCase):

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "origin": "New York, NY",
            "destination": "Boston, MA",
            "departure_utc": (
                django_timezone.now() + timedelta(hours=2)
            ).isoformat(),
            "load_lb": 20000,
            "interval_miles": 50,
        }

    def test_health_endpoint_works(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    @patch("api.services.trip_analysis.get_routes")
    @patch("api.services.trip_analysis.geocode_location")
    def test_analyzes_trip_from_api_request(
        self,
        mock_geocode,
        mock_routes,
        mock_weather,
    ):
        mock_geocode.side_effect = [
            {"name": "Origin", "latitude": 40.7128, "longitude": -74.0060},
            {"name": "Destination", "latitude": 42.3601, "longitude": -71.0589},
        ]
        mock_routes.return_value = [{
            "id": 7,
            "distance_miles": 215,
            "duration_seconds": 14400,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-74.0060, 40.7128],
                    [-73.5, 41.0],
                    [-72.8, 41.5],
                    [-71.0589, 42.3601],
                ],
            },
        }]

        def available_forecast(checkpoint):
            eta = datetime.fromisoformat(checkpoint["eta"])
            weather_time = eta.replace(minute=0, second=0, microsecond=0)
            return {
                "available": True,
                "records": [{
                    "time": weather_time,
                    "wind_mph": 15.0,
                    "rain_inches": 0.0,
                    "snow_inches": 0.0,
                    "available": True,
                }],
                "reason": None,
            }

        mock_weather.side_effect = available_forecast

        response = self.client.post(
            "/api/analyze",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("origin", response.data)
        self.assertIn("destination", response.data)
        self.assertEqual(response.data["route_count"], 1)
        self.assertEqual(len(response.data["routes"]), 1)
        route = response.data["routes"][0]
        self.assertTrue(route["scoring_available"])
        self.assertIn("score", route)
        self.assertEqual(route["rank"], 1)
        self.assertTrue(route["recommended"])
        self.assertEqual(response.data["recommendation_route_id"], 7)
        self.assertGreater(len(route["checkpoints"]), 0)
        self.assertIn("risk_label", route["checkpoints"][0])

    @patch("api.views.analyze_trip", side_effect=GeocodingError("No location found."))
    def test_returns_gateway_error_for_geocoding_failure(self, mock_analyze):
        response = self.client.post(
            "/api/analyze",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["detail"], "No location found.")

    @patch("api.views.analyze_trip", side_effect=RoutingError("Provider unavailable."))
    def test_returns_gateway_error_for_routing_failure(self, mock_analyze):
        response = self.client.post(
            "/api/analyze",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["detail"], "Provider unavailable.")
