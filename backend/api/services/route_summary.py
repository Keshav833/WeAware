from api.services.risk import RiskLevel


RISK_LABELS = {
    RiskLevel.LOW: "Low",
    RiskLevel.MODERATE: "Moderate",
    RiskLevel.HIGH: "High",
    RiskLevel.SEVERE: "Severe",
    RiskLevel.NO_TRAVEL: "No Travel",
}


def summarize_route(checkpoints: list[dict]) -> dict:
    """Summarize risk levels and weather availability for a route."""
    counts = {level.name: 0 for level in RiskLevel}
    known_scores = []
    unknown_count = 0

    for checkpoint in checkpoints:
        risk_level = checkpoint.get("risk_level")

        if risk_level is None:
            unknown_count += 1
            continue

        try:
            level = RiskLevel(risk_level)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid checkpoint risk level: {risk_level}")

        counts[level.name] += 1
        known_scores.append(int(level))

    highest_risk = (
        RISK_LABELS[RiskLevel(max(known_scores))]
        if known_scores
        else "Unknown"
    )

    return {
        "checkpoint_count": len(checkpoints),
        "risk_counts": {
            RISK_LABELS[level]: counts[level.name]
            for level in RiskLevel
        },
        "average_risk_score": (
            sum(known_scores) / len(known_scores)
            if known_scores
            else None
        ),
        "highest_risk": highest_risk,
        "has_no_travel": counts[RiskLevel.NO_TRAVEL.name] > 0,
        "unknown_weather_count": unknown_count,
        "known_checkpoint_count": len(known_scores),
    }