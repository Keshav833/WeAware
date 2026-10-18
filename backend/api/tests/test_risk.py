
from django.test import SimpleTestCase

from api.services.risk import RiskLevel, wind_level


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
