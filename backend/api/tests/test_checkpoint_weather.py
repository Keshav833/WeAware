from datetime import datetime, timezone
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.checkpoint_weather import fetch_checkpoint_weather


class CheckpointWeatherTests(SimpleTestCase):

    def setUp(self):
        self.checkpoint = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "eta": datetime(2026, 10, 18, 10, 30, tzinfo=timezone.utc),
        }

    @patch("api.services.checkpoint_weather.normalize_weather_data")
    @patch("api.services.checkpoint_weather.get_weather_forecast")
    def test_fetches_and_normalizes_weather(self, mock_fetch, mock_normalize):
        mock_fetch.return_value = {"hourly": "mock"}
        mock_normalize.return_value = [{"available": True}]

        result = fetch_checkpoint_weather(self.checkpoint)

        self.assertEqual(result, [{"available": True}])
        mock_fetch.assert_called_once()
        mock_normalize.assert_called_once_with({"hourly": "mock"})

        kwargs = mock_fetch.call_args.kwargs
        self.assertEqual(kwargs["latitude"], 40.7128)
        self.assertEqual(kwargs["longitude"], -74.0060)
        self.assertEqual(kwargs["start_date"], "2026-10-18")
        self.assertEqual(kwargs["end_date"], "2026-10-20")

    def test_rejects_naive_eta(self):
        checkpoint = {**self.checkpoint, "eta": datetime(2026, 10, 18, 10, 30)}

        with self.assertRaises(ValueError):
            fetch_checkpoint_weather(checkpoint)

    def test_rejects_invalid_forecast_horizon(self):
        with self.assertRaises(ValueError):
            fetch_checkpoint_weather(self.checkpoint, forecast_hours=0)
