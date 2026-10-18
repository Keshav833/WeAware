from datetime import timezone

from django.test import SimpleTestCase

from api.services.weather_processing import normalize_weather_data


class WeatherProcessingTests(SimpleTestCase):

    def test_normalizes_weather_units(self):
        hourly = {
            "time": ["2026-10-18T10:00", "2026-10-18T11:00Z"],
            "wind_speed_10m": [20, 30],
            "rain": [0.1, 0.2],
            "showers": [0.05, 0.0],
            "snowfall": [2.54, 5.08],
        }

        result = normalize_weather_data(hourly)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["wind_mph"], 20.0)
        self.assertAlmostEqual(result[0]["rain_inches"], 0.15)
        self.assertAlmostEqual(result[0]["snow_inches"], 1.0)
        self.assertEqual(result[0]["time"].tzinfo, timezone.utc)
        self.assertTrue(result[0]["available"])

    def test_marks_missing_weather_unavailable(self):
        hourly = {
            "time": ["2026-10-18T10:00"],
            "wind_speed_10m": [None],
            "rain": [0.0],
            "showers": [0.0],
            "snowfall": [0.0],
        }

        result = normalize_weather_data(hourly)

        self.assertFalse(result[0]["available"])
        self.assertIsNone(result[0]["wind_mph"])

    def test_rejects_inconsistent_lengths(self):
        hourly = {
            "time": ["2026-10-18T10:00"],
            "wind_speed_10m": [20, 30],
            "rain": [0.0],
            "showers": [0.0],
            "snowfall": [0.0],
        }

        with self.assertRaises(ValueError):
            normalize_weather_data(hourly)

    def test_rejects_negative_measurements(self):
        hourly = {
            "time": ["2026-10-18T10:00"],
            "wind_speed_10m": [-1],
            "rain": [0.0],
            "showers": [0.0],
            "snowfall": [0.0],
        }

        with self.assertRaises(ValueError):
            normalize_weather_data(hourly)