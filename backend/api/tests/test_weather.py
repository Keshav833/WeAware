from unittest.mock import patch

import httpx
from django.test import SimpleTestCase

from api.clients.weather import (
    WeatherError,
    get_weather_forecast,
)


class WeatherClientTests(SimpleTestCase):

    @patch("api.clients.weather.httpx.get")
    def test_fetches_hourly_forecast(self, mock_get):
        mock_response = httpx.Response(
            200,
            json={
                "hourly": {
                    "time": ["2026-10-18T10:00", "2026-10-18T11:00"],
                    "wind_speed_10m": [20.0, 30.0],
                    "rain": [0.0, 0.1],
                    "showers": [0.0, 0.0],
                    "snowfall": [0.0, 0.0],
                }
            },
            request=httpx.Request("GET", "https://api.open-meteo.com"),
        )
        mock_get.return_value = mock_response

        result = get_weather_forecast(
            latitude=40.7128,
            longitude=-74.0060,
            start_date="2026-10-18",
            end_date="2026-10-19",
        )

        self.assertEqual(len(result["time"]), 2)
        self.assertEqual(result["wind_speed_10m"][1], 30.0)

        mock_get.assert_called_once()
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["wind_speed_unit"], "mph")
        self.assertEqual(params["precipitation_unit"], "inch")
        self.assertEqual(params["timezone"], "UTC")

    @patch("api.clients.weather.httpx.get")
    def test_raises_error_for_http_failure(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        with self.assertRaises(WeatherError):
            get_weather_forecast(
                40.7128,
                -74.0060,
                "2026-10-18",
                "2026-10-19",
            )

    @patch("api.clients.weather.httpx.get")
    def test_rejects_missing_hourly_data(self, mock_get):
        mock_get.return_value = httpx.Response(
            200,
            json={"latitude": 40.7},
            request=httpx.Request("GET", "https://api.open-meteo.com"),
        )

        with self.assertRaises(WeatherError):
            get_weather_forecast(
                40.7128,
                -74.0060,
                "2026-10-18",
                "2026-10-19",
            )