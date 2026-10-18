from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from api.services.route_pipeline import analyze_route


class RoutePipelineTests(SimpleTestCase):

    def test_analyzes_route_and_returns_summary(self):
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

        # First generate the checkpoints so the test provides one
        # weather-record list for each checkpoint.
        from api.services.route_analysis import build_route_checkpoints

        generated = build_route_checkpoints(
            route,
            departure,
            interval_miles=10,
        )

        weather_by_checkpoint = []

        for checkpoint in generated["checkpoints"]:
            eta = datetime.fromisoformat(checkpoint["eta"])
            weather_time = eta.replace(
                minute=0, second=0, microsecond=0
            )

            weather_by_checkpoint.append([
                {
                    "time": weather_time,
                    "wind_mph": 15.0,
                    "rain_inches": 0.0,
                    "snow_inches": 0.0,
                    "available": True,
                }
            ])

        result = analyze_route(
            route=route,
            departure_utc=departure,
            weather_by_checkpoint=weather_by_checkpoint,
            load_lb=10000,
            interval_miles=10,
        )

        self.assertEqual(result["route_id"], 1)
        self.assertGreater(len(result["checkpoints"]), 0)
        self.assertIn("summary", result)
        self.assertEqual(
            result["summary"]["checkpoint_count"],
            len(result["checkpoints"]),
        )

    def test_rejects_mismatched_weather_count(self):
        from unittest.mock import patch
        from datetime import datetime, timezone

        departure = datetime.now(timezone.utc)

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

        fake_checkpoints = {
            "route_id": 1,
            "route_distance_miles": 100,
            "duration_seconds": 7200,
            "checkpoints": [
                {
                    "distance_miles": 10,
                    "latitude": 40.72,
                    "longitude": -74.0,
                    "eta": departure.isoformat(),
                }
            ],
        }

        with patch(
            "api.services.route_pipeline.build_route_checkpoints",
            return_value=fake_checkpoints,
        ):
            with self.assertRaises(ValueError):
                analyze_route(
                    route=route,
                    departure_utc=departure,
                    weather_by_checkpoint=[],
                    load_lb=10000,
                    interval_miles=10,
                )