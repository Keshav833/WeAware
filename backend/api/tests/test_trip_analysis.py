from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.trip_analysis import analyze_trip


class TripAnalysisTests(SimpleTestCase):

    @patch("api.services.trip_analysis.analyze_route_with_weather")
    @patch("api.services.trip_analysis.get_routes")
    @patch("api.services.trip_analysis.geocode_location")
    def test_analyzes_returned_routes(
        self,
        mock_geocode,
        mock_routes,
        mock_analyze,
    ):
        mock_geocode.side_effect = [
            {"name": "Origin", "latitude": 40.7, "longitude": -74.0},
            {"name": "Destination", "latitude": 41.0, "longitude": -73.5},
        ]
        mock_routes.return_value = [{
            "id": 1,
            "distance_miles": 100,
            "duration_seconds": 7200,
            "geometry": {
                "type": "LineString",
                "coordinates": [[-74.0, 40.7], [-73.5, 41.0]],
            },
        }]
        mock_analyze.return_value = {
            "distance_miles": 100,
            "duration_seconds": 7200,
            "checkpoints": [],
            "summary": {},
        }

        result = analyze_trip(
            origin="Origin",
            destination="Destination",
            departure_utc=datetime.now(timezone.utc) + timedelta(hours=1),
            load_lb=10000,
            interval_miles=25,
        )

        self.assertEqual(result["route_count"], 1)
        self.assertEqual(len(result["routes"]), 1)
        self.assertEqual(
            result["routes"][0]["geometry"],
            mock_routes.return_value[0]["geometry"],
        )
        self.assertIsNone(result["recommendation_route_id"])
        self.assertFalse(result["routes"][0]["scoring_available"])
        mock_geocode.assert_any_call("Origin")
        mock_geocode.assert_any_call("Destination")
        mock_analyze.assert_called_once()

    @patch("api.services.trip_analysis.analyze_route_with_weather")
    @patch("api.services.trip_analysis.get_routes")
    @patch("api.services.trip_analysis.geocode_location")
    def test_recommends_best_fully_scored_route(
        self,
        mock_geocode,
        mock_routes,
        mock_analyze,
    ):
        mock_geocode.side_effect = [
            {"name": "Origin", "latitude": 40.7, "longitude": -74.0},
            {"name": "Destination", "latitude": 41.0, "longitude": -73.5},
        ]
        mock_routes.return_value = [
            {"id": 1},
            {"id": 2},
        ]
        mock_analyze.side_effect = [
            {
                "distance_miles": 100,
                "duration_seconds": 7200,
                "checkpoints": [{"distance_miles": 50, "risk_level": 3}],
            },
            {
                "distance_miles": 100,
                "duration_seconds": 7500,
                "checkpoints": [{"distance_miles": 50, "risk_level": 1}],
            },
        ]

        result = analyze_trip(
            origin="Origin",
            destination="Destination",
            departure_utc=datetime.now(timezone.utc) + timedelta(hours=1),
            load_lb=10000,
        )

        self.assertEqual(result["recommendation_route_id"], 2)
        self.assertTrue(result["routes"][1]["recommended"])
        self.assertEqual(result["routes"][1]["rank"], 1)
        self.assertIn("estimates", result["recommendation_note"])
