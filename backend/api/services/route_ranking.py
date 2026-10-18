def rank_routes(routes: list[dict]) -> list[dict]:
    """
    Rank routes using the assignment's specified priorities.

    Routes must include:
      severe_miles
      high_miles
      average_risk_score
      duration_seconds

    Routes with incomplete or invalid scoring data are rejected.
    """
    if not routes:
        return []

    required_fields = [
        "severe_miles",
        "high_miles",
        "average_risk_score",
        "duration_seconds",
    ]

    validated_routes = []

    for route in routes:
        for field in required_fields:
            if route.get(field) is None:
                raise ValueError(
                    f"Route {route.get('route_id', 'unknown')} "
                    f"is missing {field}."
                )

        severe = route["severe_miles"]
        high = route["high_miles"]
        average = route["average_risk_score"]
        duration = route["duration_seconds"]

        if severe < 0 or high < 0 or duration < 0:
            raise ValueError("Risk miles and duration cannot be negative.")

        if average < 0 or average > 4:
            raise ValueError("Average risk score must be between 0 and 4.")

        validated_routes.append(route.copy())

    ranked = sorted(
        validated_routes,
        key=lambda route: (
            route["severe_miles"],
            route["high_miles"],
            route["average_risk_score"],
            route["duration_seconds"],
        ),
    )

    for index, route in enumerate(ranked, start=1):
        route["rank"] = index
        route["recommended"] = index == 1

    return ranked