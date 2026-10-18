from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from api.services.weather_matching import match_weather_to_checkpoint


class WeatherMatchingTests(SimpleTestCase):

    def setUp(self):
        self.base_time = datetime(
            2026, 10, 18, 10, 0, tzinfo=timezone.utc
        )

        self.records = [
            {
                "time": self.base_time,
                "wind_mph": 20.0,
                "rain_inches": 0.0,
                "snow_inches": 0.0,
                "available": True,
            },
            {
                "time": self.base_time + timedelta(hours=1),
                "wind_mph": 30.0,
                "rain_inches": 0.1,
                "snow_inches": 0.0,
                "available": True,
            },
        ]

    def test_matches_checkpoint_to_correct_hour(self):
        checkpoint = {
            "eta": self.base_time + timedelta(hours=1, minutes=20)
        }

        result = match_weather_to_checkpoint(
            checkpoint, self.records
        )

        self.assertTrue(result["available"])
        self.assertEqual(result["wind_mph"], 30.0)

    def test_rejects_stale_forecast(self):
        checkpoint = {
            "eta": self.base_time + timedelta(hours=2)
        }

        result = match_weather_to_checkpoint(
            checkpoint, self.records
        )

        self.assertFalse(result["available"])

    def test_rejects_naive_eta(self):
        checkpoint = {"eta": datetime(2026, 10, 18, 10, 30)}

        with self.assertRaises(ValueError):
            match_weather_to_checkpoint(checkpoint, self.records)

    def test_rejects_incomplete_weather(self):
        records = [
            {
                "time": self.base_time,
                "wind_mph": None,
                "rain_inches": None,
                "snow_inches": None,
                "available": False,
            }
        ]

        checkpoint = {
            "eta": self.base_time + timedelta(minutes=20)
        }

        result = match_weather_to_checkpoint(checkpoint, records)

        self.assertFalse(result["available"])