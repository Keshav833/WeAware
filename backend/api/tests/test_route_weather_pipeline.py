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
        forecast = result["checkpoints"][0]["forecast"]
        self.assertEqual(len(forecast), 49)
        self.assertEqual(forecast[0]["forecast_hour"], 0)
        self.assertEqual(
            forecast[0]["forecast_time"],
            self.departure.isoformat(),
        )
        self.assertTrue(forecast[0]["weather_available"])
        self.assertEqual(forecast[0]["risk_label"], "Low")

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
            self.assertEqual(len(checkpoint["forecast"]), 49)
            self.assertTrue(all(
                not forecast_hour["weather_available"]
                and forecast_hour["risk_label"] == "Unknown"
                for forecast_hour in checkpoint["forecast"]
            ))

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    def test_forecast_risk_changes_with_selected_hour(self, mock_weather):
        mock_weather.return_value = {
            "available": True,
            "records": [
                {
                    "time": self.departure,
                    "wind_mph": 15.0,
                    "rain_inches": 0.0,
                    "snow_inches": 0.0,
                    "available": True,
                },
                {
                    "time": self.departure + timedelta(hours=1),
                    "wind_mph": 30.0,
                    "rain_inches": 0.0,
                    "snow_inches": 0.0,
                    "available": True,
                },
            ],
            "reason": None,
        }

        result = analyze_route_with_weather(
            route=self.route,
            departure_utc=self.departure,
            load_lb=10000,
            interval_miles=10,
        )

        forecast = result["checkpoints"][0]["forecast"]
        self.assertEqual(forecast[0]["risk_label"], "Low")
        self.assertEqual(forecast[1]["risk_label"], "Moderate")

    @patch("api.services.route_weather_pipeline.safe_fetch_checkpoint_weather")
    def test_forecast_risk_uses_truck_load(self, mock_weather):
        mock_weather.return_value = {
            "available": True,
            "records": [{
                "time": self.departure,
                "wind_mph": 46.0,
                "rain_inches": 0.0,
                "snow_inches": 0.0,
                "available": True,
            }],
            "reason": None,
        }

        light_load = analyze_route_with_weather(
            route=self.route,
            departure_utc=self.departure,
            load_lb=20000,
            interval_miles=10,
        )
        heavy_load = analyze_route_with_weather(
            route=self.route,
            departure_utc=self.departure,
            load_lb=35001,
            interval_miles=10,
        )

        self.assertEqual(
            light_load["checkpoints"][0]["forecast"][0]["risk_label"],
            "Severe",
        )
        self.assertEqual(
            heavy_load["checkpoints"][0]["forecast"][0]["risk_label"],
            "No Travel",
        )

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
