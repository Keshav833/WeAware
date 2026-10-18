from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.trip_analysis import analyze_trip


class TripEdgeCaseTests(SimpleTestCase):

    def setUp(self):
        self.departure = datetime.now(timezone.utc) + timedelta(hours=1)

    @patch("api.services.trip_analysis.get_routes", return_value=[])
    @patch("api.services.trip_analysis.geocode_location")
    def test_handles_no_routes(self, mock_geocode, mock_routes):
        mock_geocode.side_effect = [
            {"name": "A", "latitude": 40.0, "longitude": -74.0},
            {"name": "B", "latitude": 41.0, "longitude": -73.0},
        ]

        result = analyze_trip(
            origin="A",
            destination="B",
            departure_utc=self.departure,
            load_lb=10000,
        )

        self.assertEqual(result["route_count"], 0)
        self.assertEqual(result["routes"], [])
        self.assertIsNone(result["recommendation_route_id"])

    @patch("api.services.trip_analysis.analyze_route_with_weather")
    @patch("api.services.trip_analysis.get_routes")
    @patch("api.services.trip_analysis.geocode_location")
    def test_ranks_two_provider_routes_without_inventing_alternatives(
        self,
        mock_geocode,
        mock_routes,
        mock_analyze,
    ):
        mock_geocode.side_effect = [
            {"name": "A", "latitude": 40.0, "longitude": -74.0},
            {"name": "B", "latitude": 41.0, "longitude": -73.0},
        ]
        mock_routes.return_value = [{"id": 1}, {"id": 2}]
        mock_analyze.side_effect = [
            {
                "distance_miles": 100,
                "duration_seconds": 7200,
                "checkpoints": [{"distance_miles": 50, "risk_level": 2}],
            },
            {
                "distance_miles": 110,
                "duration_seconds": 7500,
                "checkpoints": [{"distance_miles": 55, "risk_level": 1}],
            },
        ]

        result = analyze_trip(
            origin="A",
            destination="B",
            departure_utc=self.departure,
            load_lb=10000,
        )

        self.assertEqual(result["route_count"], 2)
        self.assertEqual(len(result["routes"]), 2)
        self.assertEqual(result["recommendation_route_id"], 2)

    @patch("api.services.trip_analysis.analyze_route_with_weather")
    @patch("api.services.trip_analysis.get_routes")
    @patch("api.services.trip_analysis.geocode_location")
    def test_unknown_weather_disables_recommendation(
        self,
        mock_geocode,
        mock_routes,
        mock_analyze,
    ):
        mock_geocode.side_effect = [
            {"name": "A", "latitude": 40.0, "longitude": -74.0},
            {"name": "B", "latitude": 41.0, "longitude": -73.0},
        ]
        mock_routes.return_value = [{"id": 1}]
        mock_analyze.return_value = {
            "distance_miles": 100,
            "duration_seconds": 7200,
            "checkpoints": [{"distance_miles": 50, "risk_level": None}],
        }

        result = analyze_trip(
            origin="A",
            destination="B",
            departure_utc=self.departure,
            load_lb=10000,
        )

        self.assertIsNone(result["recommendation_route_id"])
        self.assertFalse(result["routes"][0]["scoring_available"])
        self.assertIsNone(result["routes"][0]["rank"])
        self.assertFalse(result["routes"][0]["recommended"])
