
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


def rain_level(rain_inches_per_hour: float) -> RiskLevel:
    """Classify rainfall intensity in inches per hour."""

    if rain_inches_per_hour < 0:
        raise ValueError("Rainfall cannot be negative.")

    if rain_inches_per_hour < 0.10:
        return RiskLevel.LOW
    if rain_inches_per_hour < 0.25:
        return RiskLevel.MODERATE
    if rain_inches_per_hour < 0.50:
        return RiskLevel.HIGH
    if rain_inches_per_hour <= 1.00:
        return RiskLevel.SEVERE

    return RiskLevel.NO_TRAVEL


def snow_level(snow_inches_per_hour: float) -> RiskLevel:
    """Classify snowfall intensity in inches per hour."""

    if snow_inches_per_hour < 0:
        raise ValueError("Snowfall cannot be negative.")

    if snow_inches_per_hour < 0.5:
        return RiskLevel.LOW
    if snow_inches_per_hour < 1.0:
        return RiskLevel.MODERATE
    if snow_inches_per_hour < 2.0:
        return RiskLevel.HIGH
    if snow_inches_per_hour <= 3.0:
        return RiskLevel.SEVERE

    return RiskLevel.NO_TRAVEL
