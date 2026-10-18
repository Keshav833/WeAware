
from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from api.serializers import AnalyzeRequestSerializer


class AnalyzeRequestSerializerTests(SimpleTestCase):

    def valid_payload(self):
        departure = (
            timezone.now() + timedelta(hours=3)
        ).isoformat()

        return {
            "origin": "New York, NY",
            "destination": "Boston, MA",
            "departure_utc": departure,
            "load_lb": 25000,
            "interval_miles": 25,
        }

    def test_valid_request(self):
        serializer = AnalyzeRequestSerializer(
            data=self.valid_payload()
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_negative_load_is_rejected(self):
        payload = self.valid_payload()
        payload["load_lb"] = -100

        serializer = AnalyzeRequestSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("load_lb", serializer.errors)

    def test_invalid_interval_is_rejected(self):
        payload = self.valid_payload()
        payload["interval_miles"] = 15

        serializer = AnalyzeRequestSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("interval_miles", serializer.errors)

    def test_identical_locations_are_rejected(self):
        payload = self.valid_payload()
        payload["destination"] = "new york, ny"

        serializer = AnalyzeRequestSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("destination", serializer.errors)
