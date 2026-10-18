from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from api.services.route_analysis import build_route_checkpoints


class RouteAnalysisTests(SimpleTestCase):
    def test_build_route_checkpoints_returns_expected_structure(self):
        departure = datetime.now(timezone.utc) + timedelta(hours=1)

        route = {
            "id": 1,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-74.0060, 40.7128],
                    [-73.9855, 40.7580],
                    [-73.9442, 40.7794],
                    [-73.8500, 40.8000],
                ],
            },
        }

        result = build_route_checkpoints(
            route=route,
            departure_utc=departure,
            interval_miles=10,
        )

        self.assertEqual(result["route_id"], 1)
        self.assertEqual(result["route_distance_miles"], 100)
        self.assertEqual(result["duration_seconds"], 7200)
        self.assertIsInstance(result["checkpoints"], list)

        for checkpoint in result["checkpoints"]:
            self.assertIn("latitude", checkpoint)
            self.assertIn("longitude", checkpoint)
            self.assertIn("distance_miles", checkpoint)
            self.assertIn("eta", checkpoint)

    def test_build_route_checkpoints_rejects_invalid_interval(self):
        departure = datetime.now(timezone.utc) + timedelta(hours=1)

        route = {
            "id": 1,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-74.0060, 40.7128],
                    [-73.9855, 40.7580],
                ],
            },
        }

        with self.assertRaises(ValueError):
            build_route_checkpoints(
                route=route,
                departure_utc=departure,
                interval_miles=15,
            )