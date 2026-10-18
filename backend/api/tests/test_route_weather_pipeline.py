from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.route_weather_pipeline import analyze_route_with_weather


class RouteWeatherPipelineTests(SimpleTestCase):

    def setUp(self):
        self.departure = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)
        self.route = {
            "id": 1,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-74.0060, 40.7128],
                    [-73.9855, 40.7580],
                    [-73.9442, 40.7794],
                    [-73.8500, 40.8000],
                ],
            },
        }

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    def test_analyzes_route_using_fetched_weather(self, mock_weather):
        mock_weather.return_value = {
            "available": True,
            "records": [{
                "time": self.departure.replace(minute=0, second=0, microsecond=0),
                "wind_mph": 15.0,
                "rain_inches": 0.0,
                "snow_inches": 0.0,
                "available": True,
            }],
            "reason": None,
        }

        result = analyze_route_with_weather(
            route=self.route,
            departure_utc=self.departure,
            load_lb=10000,
            interval_miles=10,
        )

        self.assertEqual(result["route_id"], 1)
        self.assertGreater(len(result["checkpoints"]), 0)
        self.assertIn("summary", result)
        self.assertGreater(mock_weather.call_count, 0)

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    def test_weather_failure_produces_unknown_risk(self, mock_weather):
        mock_weather.return_value = {
            "available": False,
            "records": [],
            "reason": "Provider unavailable",
        }

        result = analyze_route_with_weather(
            route=self.route,
            departure_utc=self.departure,
            load_lb=10000,
            interval_miles=10,
        )

        self.assertGreater(len(result["checkpoints"]), 0)
        for checkpoint in result["checkpoints"]:
            self.assertEqual(checkpoint["risk_label"], "Unknown")
            self.assertIsNone(checkpoint["risk_level"])

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    def test_rejects_invalid_load(self, mock_weather):
        with self.assertRaises(ValueError):
            analyze_route_with_weather(
                route=self.route,
                departure_utc=self.departure,
                load_lb=0,
                interval_miles=10,
            )

        mock_weather.assert_not_called()
