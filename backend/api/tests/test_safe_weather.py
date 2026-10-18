from unittest.mock import patch

from django.test import SimpleTestCase

from api.clients.weather import WeatherError
from api.services.safe_weather import safe_fetch_checkpoint_weather


class SafeWeatherTests(SimpleTestCase):

    @patch("api.services.safe_weather.fetch_checkpoint_weather")
    def test_returns_available_weather(self, mock_fetch):
        records = [{"available": True}]
        mock_fetch.return_value = records

        result = safe_fetch_checkpoint_weather({
            "latitude": 40.7,
            "longitude": -74.0,
            "eta": "2026-10-18T10:30:00+00:00",
        })

        self.assertTrue(result["available"])
        self.assertEqual(result["records"], records)
        self.assertIsNone(result["reason"])

    @patch("api.services.safe_weather.fetch_checkpoint_weather")
    def test_handles_provider_error(self, mock_fetch):
        mock_fetch.side_effect = WeatherError("Provider unavailable")

        result = safe_fetch_checkpoint_weather({
            "latitude": 40.7,
            "longitude": -74.0,
            "eta": "2026-10-18T10:30:00+00:00",
        })

        self.assertFalse(result["available"])
        self.assertEqual(result["records"], [])
        self.assertIn("Provider unavailable", result["reason"])

    @patch("api.services.safe_weather.fetch_checkpoint_weather")
    def test_handles_empty_forecast(self, mock_fetch):
        mock_fetch.return_value = []

        result = safe_fetch_checkpoint_weather({
            "latitude": 40.7,
            "longitude": -74.0,
            "eta": "2026-10-18T10:30:00+00:00",
        })

        self.assertFalse(result["available"])
        self.assertEqual(result["records"], [])
