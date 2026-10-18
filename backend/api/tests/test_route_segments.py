from django.test import SimpleTestCase

from api.services.route_segments import build_risk_segments


class RouteSegmentsTests(SimpleTestCase):

    def test_builds_distance_segments(self):
        result = build_risk_segments(
            [
                {"distance_miles": 25, "risk_level": 2},
                {"distance_miles": 75, "risk_level": 3},
            ],
            100,
        )

        self.assertEqual(result, [
            {
                "start_miles": 0.0,
                "end_miles": 50.0,
                "risk_level": 2,
            },
            {
                "start_miles": 50.0,
                "end_miles": 100.0,
                "risk_level": 3,
            },
        ])

    def test_empty_checkpoints_produce_unknown_segment(self):
        result = build_risk_segments([], 100)

        self.assertIsNone(result[0]["risk_level"])
        self.assertEqual(result[0]["end_miles"], 100)

    def test_rejects_checkpoint_outside_route(self):
        with self.assertRaises(ValueError):
            build_risk_segments(
                [{"distance_miles": 120, "risk_level": 2}],
                100,
            )

    def test_rejects_duplicate_checkpoint_distances(self):
        with self.assertRaises(ValueError):
            build_risk_segments(
                [
                    {"distance_miles": 25, "risk_level": 2},
                    {"distance_miles": 25, "risk_level": 3},
                ],
                100,
            )
