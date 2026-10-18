from django.test import SimpleTestCase

from api.services.route_ranking import rank_routes, rank_scored_routes


class RouteRankingTests(SimpleTestCase):

    def test_prioritizes_fewer_severe_miles(self):
        routes = [
            {
                "route_id": 1,
                "severe_miles": 20,
                "high_miles": 0,
                "average_risk_score": 1.0,
                "duration_seconds": 3000,
            },
            {
                "route_id": 2,
                "severe_miles": 10,
                "high_miles": 30,
                "average_risk_score": 2.0,
                "duration_seconds": 4000,
            },
        ]

        result = rank_routes(routes)

        self.assertEqual(result[0]["route_id"], 2)
        self.assertTrue(result[0]["recommended"])

    def test_uses_high_miles_as_second_priority(self):
        routes = [
            {
                "route_id": 1,
                "severe_miles": 10,
                "high_miles": 20,
                "average_risk_score": 1.0,
                "duration_seconds": 2000,
            },
            {
                "route_id": 2,
                "severe_miles": 10,
                "high_miles": 10,
                "average_risk_score": 2.0,
                "duration_seconds": 3000,
            },
        ]

        result = rank_routes(routes)

        self.assertEqual(result[0]["route_id"], 2)

    def test_uses_average_risk_as_third_priority(self):
        routes = [
            {
                "route_id": 1,
                "severe_miles": 5,
                "high_miles": 10,
                "average_risk_score": 2.0,
                "duration_seconds": 1000,
            },
            {
                "route_id": 2,
                "severe_miles": 5,
                "high_miles": 10,
                "average_risk_score": 1.0,
                "duration_seconds": 2000,
            },
        ]

        result = rank_routes(routes)

        self.assertEqual(result[0]["route_id"], 2)

    def test_uses_duration_as_final_tiebreaker(self):
        routes = [
            {
                "route_id": 1,
                "severe_miles": 0,
                "high_miles": 10,
                "average_risk_score": 1.0,
                "duration_seconds": 4000,
            },
            {
                "route_id": 2,
                "severe_miles": 0,
                "high_miles": 10,
                "average_risk_score": 1.0,
                "duration_seconds": 3000,
            },
        ]

        result = rank_routes(routes)

        self.assertEqual(result[0]["route_id"], 2)

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(rank_routes([]), [])

    def test_rejects_missing_scoring_data(self):
        with self.assertRaises(ValueError):
            rank_routes([{"route_id": 1}])

    def test_rank_scored_routes_excludes_incomplete_routes(self):
        result = rank_scored_routes([
            {
                "route_id": 1,
                "scoring_available": False,
                "score": None,
            },
            {
                "route_id": 2,
                "scoring_available": True,
                "score": {
                    "severe_miles": 0,
                    "high_miles": 5,
                    "average_risk_score": 1.0,
                    "duration_seconds": 3000,
                },
            },
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["route_id"], 2)
        self.assertEqual(result[0]["rank"], 1)
        self.assertTrue(result[0]["recommended"])