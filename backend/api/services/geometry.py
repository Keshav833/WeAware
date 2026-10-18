
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_MILES = 3958.7613

# Measures the route using the supplied coordinates.
# Places checkpoints at each selected interval.
# Interpolates coordinates along the route segments.
# Estimates arrival times proportionally to distance travelled.
# Leaves the destination out of the intermediate checkpoint list.

@dataclass(frozen=True)
class Checkpoint:
    distance_miles: float
    latitude: float
    longitude: float
    eta: datetime


def haversine_miles(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate great-circle distance between two coordinates."""

    lat1, lon1, lat2, lon2 = map(
        radians, (lat1, lon1, lat2, lon2)
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_MILES * asin(sqrt(min(1.0, a)))


def interpolate_point(
    start: tuple[float, float],
    end: tuple[float, float],
    fraction: float,
) -> tuple[float, float]:
    """Linearly interpolate latitude and longitude."""

    lat = start[0] + (end[0] - start[0]) * fraction
    lon = start[1] + (end[1] - start[1]) * fraction

    return lat, lon


def generate_checkpoints(
    coordinates: list[tuple[float, float]],
    departure: datetime,
    total_duration_seconds: float,
    interval_miles: int = 25,
) -> list[Checkpoint]:
    """
    Generate checkpoints along a route.

    Coordinates use (latitude, longitude).
    Arrival times are estimated proportionally to distance.
    """

    if len(coordinates) < 2:
        raise ValueError("Route needs at least two coordinates.")

    if departure.tzinfo is None or departure.utcoffset() is None:
        raise ValueError("Departure must be timezone-aware.")

    if total_duration_seconds < 0:
        raise ValueError("Duration cannot be negative.")

    if interval_miles not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25 or 50 miles.")

    segment_distances = [
        haversine_miles(*start, *end)
        for start, end in zip(coordinates, coordinates[1:])
    ]

    total_distance = sum(segment_distances)

    if total_distance <= 0:
        raise ValueError("Route distance must be positive.")

    checkpoints = []
    cumulative_distance = 0.0
    segment_index = 0

    target_distance = float(interval_miles)

    while target_distance < total_distance:
        while (
            segment_index < len(segment_distances) - 1
            and cumulative_distance
            + segment_distances[segment_index]
            < target_distance
        ):
            cumulative_distance += segment_distances[segment_index]
            segment_index += 1

        segment_distance = segment_distances[segment_index]

        fraction = (
            (target_distance - cumulative_distance) / segment_distance
            if segment_distance > 0
            else 0.0
        )

        start = coordinates[segment_index]
        end = coordinates[segment_index + 1]

        latitude, longitude = interpolate_point(
            start, end, fraction
        )

        elapsed_seconds = (
            target_distance / total_distance
        ) * total_duration_seconds

        checkpoints.append(
            Checkpoint(
                distance_miles=target_distance,
                latitude=latitude,
                longitude=longitude,
                eta=departure + timedelta(seconds=elapsed_seconds),
            )
        )

        target_distance += interval_miles

    return checkpoints
