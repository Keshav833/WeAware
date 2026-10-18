
from enum import IntEnum


class RiskLevel(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


def wind_level(wind_mph: float) -> RiskLevel:
    """Classify wind speed in miles per hour."""

    if wind_mph < 0:
        raise ValueError("Wind speed cannot be negative.")

    if wind_mph < 25:
        return RiskLevel.LOW
    if wind_mph < 35:
        return RiskLevel.MODERATE
    if wind_mph < 45:
        return RiskLevel.HIGH
    if wind_mph < 55:
        return RiskLevel.SEVERE

    return RiskLevel.NO_TRAVEL
