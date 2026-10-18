from django.test import SimpleTestCase

from api.services.route_comparison import score_route


class RouteComparisonTests(SimpleTestCase):

    def test_scores_route_with_complete_weather(self):
        route = {
            "route_id": 1,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "checkpoints": [
                {"distance_miles": 25, "risk_level": 3},
                {"distance_miles": 75, "risk_level": 1},
            ],
        }

        result = score_route(route)

        self.assertTrue(result["scoring_available"])
        self.assertEqual(result["score"]["severe_miles"], 50)
        self.assertEqual(result["score"]["high_miles"], 0)

    def test_refuses_to_score_incomplete_weather(self):
        route = {
            "route_id": 2,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "checkpoints": [
                {"distance_miles": 25, "risk_level": 3},
                {"distance_miles": 75, "risk_level": None},
            ],
        }

        result = score_route(route)

        self.assertFalse(result["scoring_available"])
        self.assertIsNone(result.get("score"))
