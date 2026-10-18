
from django.test import SimpleTestCase

from api.services.risk import (
    RiskLevel,
    wind_level,
    rain_level,
    snow_level,
)

class WindRiskTests(SimpleTestCase):

    def test_wind_thresholds(self):
        cases = [
            (0, RiskLevel.LOW),
            (24.9, RiskLevel.LOW),
            (25, RiskLevel.MODERATE),
            (34.9, RiskLevel.MODERATE),
            (35, RiskLevel.HIGH),
            (44.9, RiskLevel.HIGH),
            (45, RiskLevel.SEVERE),
            (54.9, RiskLevel.SEVERE),
            (55, RiskLevel.NO_TRAVEL),
            (70, RiskLevel.NO_TRAVEL),
        ]

        for speed, expected in cases:
            with self.subTest(speed=speed):
                self.assertEqual(wind_level(speed), expected)

    def test_negative_wind_is_rejected(self):
        with self.assertRaises(ValueError):
            wind_level(-1)


class RainRiskTests(SimpleTestCase):

    def test_rain_thresholds(self):
        cases = [
            (0, RiskLevel.LOW),
            (0.099, RiskLevel.LOW),
            (0.10, RiskLevel.MODERATE),
            (0.249, RiskLevel.MODERATE),
            (0.25, RiskLevel.HIGH),
            (0.499, RiskLevel.HIGH),
            (0.50, RiskLevel.SEVERE),
            (1.00, RiskLevel.SEVERE),
            (1.001, RiskLevel.NO_TRAVEL),
            (1.50, RiskLevel.NO_TRAVEL),
        ]

        for rainfall, expected in cases:
            with self.subTest(rainfall=rainfall):
                self.assertEqual(
                    rain_level(rainfall),
                    expected,
                )

    def test_negative_rainfall_is_rejected(self):
        with self.assertRaises(ValueError):
            rain_level(-0.1)


class SnowRiskTests(SimpleTestCase):

    def test_snow_thresholds(self):
        cases = [
            (0, RiskLevel.LOW),
            (0.499, RiskLevel.LOW),
            (0.5, RiskLevel.MODERATE),
            (0.999, RiskLevel.MODERATE),
            (1.0, RiskLevel.HIGH),
            (1.999, RiskLevel.HIGH),
            (2.0, RiskLevel.SEVERE),
            (3.0, RiskLevel.SEVERE),
            (3.001, RiskLevel.NO_TRAVEL),
            (4.0, RiskLevel.NO_TRAVEL),
        ]

        for snowfall, expected in cases:
            with self.subTest(snowfall=snowfall):
                self.assertEqual(
                    snow_level(snowfall),
                    expected,
                )

    def test_negative_snowfall_is_rejected(self):
        with self.assertRaises(ValueError):
            snow_level(-0.1)
