from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from api.services.checkpoint_analysis import analyze_checkpoint


class CheckpointAnalysisTests(SimpleTestCase):

    def setUp(self):
        self.eta = datetime(
            2026, 10, 18, 10, 30, tzinfo=timezone.utc
        )

        self.checkpoint = {
            "distance_miles": 25,
            "latitude": 40.7,
            "longitude": -74.0,
            "eta": self.eta,
        }

        self.weather_records = [
            {
                "time": self.eta.replace(minute=0),
                "wind_mph": 20.0,
                "rain_inches": 0.0,
                "snow_inches": 0.0,
                "available": True,
            }
        ]

    def test_calculates_low_risk(self):
        result = analyze_checkpoint(
            self.checkpoint,
            self.weather_records,
            load_lb=10000,
        )

        self.assertTrue(result["weather_available"])
        self.assertEqual(result["risk_label"], "Low")
        self.assertEqual(result["risk_level"], 0)

    def test_applies_load_override(self):
        records = [
            {
                **self.weather_records[0],
                "wind_mph": 46.0,
            }
        ]

        result = analyze_checkpoint(
            self.checkpoint,
            records,
            load_lb=35000,
        )

        self.assertEqual(result["risk_label"], "No Travel")

    def test_unknown_when_weather_is_missing(self):
        records = [
            {
                **self.weather_records[0],
                "available": False,
                "wind_mph": None,
                "rain_inches": None,
                "snow_inches": None,
            }
        ]

        result = analyze_checkpoint(
            self.checkpoint,
            records,
            load_lb=10000,
        )

        self.assertFalse(result["weather_available"])
        self.assertEqual(result["risk_label"], "Unknown")
        self.assertIsNone(result["risk_level"])

    def test_rejects_invalid_load(self):
        with self.assertRaises(ValueError):
            analyze_checkpoint(
                self.checkpoint,
                self.weather_records,
                load_lb=0,
            )