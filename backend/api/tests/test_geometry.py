
from datetime import datetime, timezone

from django.test import SimpleTestCase

from api.services.geometry import (
    generate_checkpoints,
    haversine_miles,
)


class GeometryTests(SimpleTestCase):

    def test_haversine_distance(self):
        # One degree of longitude at the equator is about 69 miles.
        distance = haversine_miles(0, 0, 0, 1)

        self.assertAlmostEqual(distance, 69.09, delta=0.2)

    def test_checkpoints_follow_interval(self):
        departure = datetime(
            2026, 10, 20, 8, 0, tzinfo=timezone.utc
        )

        coordinates = [(0, 0), (0, 1)]

        checkpoints = generate_checkpoints(
            coordinates=coordinates,
            departure=departure,
            total_duration_seconds=6900,
            interval_miles=25,
        )

        self.assertEqual(
            [cp.distance_miles for cp in checkpoints],
            [25.0, 50.0],
        )

        self.assertAlmostEqual(
            checkpoints[0].latitude, 0.0
        )

        self.assertGreater(checkpoints[0].longitude, 0.0)
        self.assertLess(checkpoints[0].longitude, 1.0)

    
def test_checkpoint_eta(self):
    departure = datetime(
        2026, 10, 20, 8, 0, tzinfo=timezone.utc
    )

    checkpoints = generate_checkpoints(
        coordinates=[(0, 0), (0, 1)],
        departure=departure,
        total_duration_seconds=6900,
        interval_miles=25,
    )

    elapsed_seconds = (
        checkpoints[0].eta - departure
    ).total_seconds()

    expected_seconds = (
        checkpoints[0].distance_miles
        / haversine_miles(0, 0, 0, 1)
    ) * 6900

    self.assertAlmostEqual(
        elapsed_seconds,
        expected_seconds,
        places=5,
    )


    def test_invalid_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_checkpoints(
                coordinates=[(0, 0), (0, 1)],
                departure=datetime.now(timezone.utc),
                total_duration_seconds=3600,
                interval_miles=15,
            )

    def test_naive_datetime_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_checkpoints(
                coordinates=[(0, 0), (0, 1)],
                departure=datetime(2026, 10, 20, 8, 0),
                total_duration_seconds=3600,
                interval_miles=25,
            )

def test_parse_route_geometry_converts_coordinates(self):
    from api.services.geometry import parse_route_geometry

    route = {
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-74.0060, 40.7128],
                [-73.9855, 40.7580],
                [-73.9442, 40.7794],
            ],
        },
        "distance_miles": 5.0,
        "duration_seconds": 1200,
    }

    result = parse_route_geometry(route)

    self.assertEqual(
        result["coordinates"],
        [
            (40.7128, -74.0060),
            (40.7580, -73.9855),
            (40.7794, -73.9442),
        ],
    )

    self.assertEqual(len(result["segment_distances_miles"]), 2)
    self.assertGreater(result["total_geometry_miles"], 0)
    self.assertEqual(result["route_distance_miles"], 5.0)
    self.assertEqual(result["duration_seconds"], 1200)


def test_parse_route_geometry_rejects_insufficient_coordinates(self):
    from api.services.geometry import parse_route_geometry

    route = {
        "geometry": {
            "coordinates": [[-74.0060, 40.7128]],
        }
    }

    with self.assertRaises(ValueError):
        parse_route_geometry(route)


def test_parse_route_geometry_rejects_invalid_latitude(self):
    from api.services.geometry import parse_route_geometry

    route = {
        "geometry": {
            "coordinates": [
                [-74.0060, 40.7128],
                [-73.9855, 95.0],
            ]
        }
    }

    with self.assertRaises(ValueError):
        parse_route_geometry(route)