from django.test import SimpleTestCase

from api.services.route_scoring import calculate_route_score


class RouteScoringTests(SimpleTestCase):

    def setUp(self):
        self.segments = [
            {"start_miles": 0, "end_miles": 20, "risk_level": 0},
            {"start_miles": 20, "end_miles": 40, "risk_level": 2},
            {"start_miles": 40, "end_miles": 60, "risk_level": 3},
            {"start_miles": 60, "end_miles": 100, "risk_level": 1},
        ]

    def test_calculates_distance_weighted_risk(self):
        result = calculate_route_score(
            self.segments,
            total_distance_miles=100,
            duration_seconds=7200,
        )

        self.assertAlmostEqual(result["severe_miles"], 20)
        self.assertAlmostEqual(result["high_miles"], 20)
        self.assertAlmostEqual(result["no_travel_miles"], 0)

        # (20*0 + 20*2 + 20*3 + 40*1) / 100 = 1.4
        self.assertAlmostEqual(result["average_risk_score"], 1.4)

    def test_detects_no_travel_miles(self):
        result = calculate_route_score(
            [
                {"start_miles": 0, "end_miles": 50, "risk_level": 0},
                {"start_miles": 50, "end_miles": 100, "risk_level": 4},
            ],
            total_distance_miles=100,
            duration_seconds=5000,
        )

        self.assertEqual(result["no_travel_miles"], 50)

    def test_rejects_gaps_between_segments(self):
        with self.assertRaises(ValueError):
            calculate_route_score(
                [
                    {"start_miles": 0, "end_miles": 40, "risk_level": 0},
                    {"start_miles": 50, "end_miles": 100, "risk_level": 2},
                ],
                total_distance_miles=100,
                duration_seconds=5000,
            )

    def test_rejects_unknown_risk(self):
        with self.assertRaises(ValueError):
            calculate_route_score(
                [
                    {"start_miles": 0, "end_miles": 100, "risk_level": None},
                ],
                total_distance_miles=100,
                duration_seconds=5000,
            )

    def test_rejects_invalid_route_distance(self):
        with self.assertRaises(ValueError):
            calculate_route_score(
                self.segments,
                total_distance_miles=0,
                duration_seconds=7200,
            )