from api.services.risk import RiskLevel


def calculate_route_score(
    risk_segments: list[dict],
    total_distance_miles: float,
    duration_seconds: float,
) -> dict:
    """
    Calculate distance-weighted route risk metrics.

    Each segment must contain:
      - start_miles
      - end_miles
      - risk_level: integer from 0 to 4

    Risk levels:
      0 = Low
      1 = Moderate
      2 = High
      3 = Severe
      4 = No Travel
    """
    if total_distance_miles <= 0:
        raise ValueError("Total route distance must be positive.")

    if duration_seconds < 0:
        raise ValueError("Route duration cannot be negative.")

    if not risk_segments:
        raise ValueError("At least one risk segment is required.")

    normalized_segments = []

    for segment in risk_segments:
        start = segment.get("start_miles")
        end = segment.get("end_miles")
        raw_risk = segment.get("risk_level")

        if start is None or end is None:
            raise ValueError("Each segment needs start and end distances.")

        if start < 0 or end <= start:
            raise ValueError("Segment distances are invalid.")

        if end > total_distance_miles:
            raise ValueError("Segment exceeds total route distance.")

        if raw_risk is None:
            raise ValueError(
                "Cannot score a route with unknown segment risk."
            )

        try:
            risk = RiskLevel(raw_risk)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid risk level: {raw_risk}")

        normalized_segments.append({
            "start_miles": float(start),
            "end_miles": float(end),
            "risk_level": risk,
        })

    normalized_segments.sort(key=lambda item: item["start_miles"])

    # Require full route coverage without gaps or overlaps.
    tolerance = 1e-6

    if abs(normalized_segments[0]["start_miles"]) > tolerance:
        raise ValueError("Risk segments must begin at mile zero.")

    if abs(normalized_segments[-1]["end_miles"] - total_distance_miles) > tolerance:
        raise ValueError("Risk segments must cover the entire route.")

    for index in range(1, len(normalized_segments)):
        previous_end = normalized_segments[index - 1]["end_miles"]
        current_start = normalized_segments[index]["start_miles"]

        if abs(previous_end - current_start) > tolerance:
            raise ValueError("Risk segments contain a gap or overlap.")

    severe_miles = 0.0
    high_miles = 0.0
    no_travel_miles = 0.0
    weighted_risk_total = 0.0

    for segment in normalized_segments:
        distance = segment["end_miles"] - segment["start_miles"]
        risk = segment["risk_level"]

        weighted_risk_total += int(risk) * distance

        if risk == RiskLevel.SEVERE:
            severe_miles += distance
        elif risk == RiskLevel.HIGH:
            high_miles += distance
        elif risk == RiskLevel.NO_TRAVEL:
            no_travel_miles += distance

    average_risk = weighted_risk_total / total_distance_miles

    return {
        "total_distance_miles": total_distance_miles,
        "severe_miles": severe_miles,
        "high_miles": high_miles,
        "no_travel_miles": no_travel_miles,
        "average_risk_score": average_risk,
        "duration_seconds": duration_seconds,
        "risk_segments_count": len(normalized_segments),
    }