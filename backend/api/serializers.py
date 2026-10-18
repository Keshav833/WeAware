
from django.utils import timezone
from rest_framework import serializers


# Validation	Reason
# Origin and destination -	    Reject empty or identical locations
# Departure time	-           Require a timezone and a future departure
# Load weight	        -       Reject zero or negative weights
# Interval	-                   Only allow 10, 25 or 50 miles
# Field lengths -            	Avoid unnecessarily long input
class AnalyzeRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
    )

    destination = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
    )

    departure_utc = serializers.DateTimeField()

    load_lb = serializers.FloatField(
        min_value=0.01,
    )

    interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25,
    )

    def validate_origin(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Origin cannot be empty."
            )
        return value.strip()

    def validate_destination(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Destination cannot be empty."
            )
        return value.strip()

    def validate_departure_utc(self, value):
        if timezone.is_naive(value):
            raise serializers.ValidationError(
                "Departure time must include a timezone."
            )

        if value <= timezone.now():
            raise serializers.ValidationError(
                "Departure time must be in the future."
            )

        return value

    def validate(self, attrs):
        if (
            attrs["origin"].casefold()
            == attrs["destination"].casefold()
        ):
            raise serializers.ValidationError({
                "destination": (
                    "Origin and destination must be different."
                )
            })

        return attrs
