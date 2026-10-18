def build_risk_segments(
    checkpoints: list[dict],
    total_distance_miles: float,
) -> list[dict]:
    if total_distance_miles <= 0:
        raise ValueError("Route distance must be positive.")

    if not checkpoints:
        return [{
            "start_miles": 0.0,
            "end_miles": total_distance_miles,
            "risk_level": None,
        }]

    ordered = sorted(
        checkpoints,
        key=lambda checkpoint: checkpoint["distance_miles"],
    )
    distances = [checkpoint["distance_miles"] for checkpoint in ordered]

    if any(
        distance < 0 or distance > total_distance_miles
        for distance in distances
    ):
        raise ValueError("Checkpoint distance is outside the route.")

    if len(set(distances)) != len(distances):
        raise ValueError("Checkpoint distances must be unique.")

    boundaries = [0.0]
    for left, right in zip(distances, distances[1:]):
        boundaries.append((left + right) / 2)
    boundaries.append(float(total_distance_miles))

    return [
        {
            "start_miles": boundaries[index],
            "end_miles": boundaries[index + 1],
            "risk_level": checkpoint.get("risk_level"),
        }
        for index, checkpoint in enumerate(ordered)
    ]
