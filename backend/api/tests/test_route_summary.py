from django.test import SimpleTestCase

from api.services.route_summary import summarize_route


class RouteSummaryTests(SimpleTestCase):

    def test_summarizes_risk_counts_and_average(self):
        checkpoints = [
            {"risk_level": 0},
            {"risk_level": 1},
            {"risk_level": 2},
            {"risk_level": 3},
        ]

        result = summarize_route(checkpoints)

        self.assertEqual(result["checkpoint_count"], 4)
        self.assertEqual(result["risk_counts"]["Low"], 1)
        self.assertEqual(result["risk_counts"]["Moderate"], 1)
        self.assertEqual(result["risk_counts"]["High"], 1)
        self.assertEqual(result["risk_counts"]["Severe"], 1)
        self.assertEqual(result["average_risk_score"], 1.5)
        self.assertEqual(result["highest_risk"], "Severe")
        self.assertFalse(result["has_no_travel"])

    def test_detects_no_travel_checkpoint(self):
        result = summarize_route([
            {"risk_level": 0},
            {"risk_level": 4},
        ])

        self.assertTrue(result["has_no_travel"])
        self.assertEqual(result["highest_risk"], "No Travel")

    def test_handles_unknown_weather(self):
        result = summarize_route([
            {"risk_level": 0},
            {"risk_level": None},
        ])

        self.assertEqual(result["unknown_weather_count"], 1)
        self.assertEqual(result["known_checkpoint_count"], 1)
        self.assertEqual(result["average_risk_score"], 0)

    def test_handles_all_unknown_weather(self):
        result = summarize_route([
            {"risk_level": None},
            {"risk_level": None},
        ])

        self.assertIsNone(result["average_risk_score"])
        self.assertEqual(result["highest_risk"], "Unknown")
        self.assertEqual(result["unknown_weather_count"], 2)

    def test_rejects_invalid_risk_level(self):
        with self.assertRaises(ValueError):
            summarize_route([{"risk_level": 99}])