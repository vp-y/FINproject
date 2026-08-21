def run_rate_hike_scenario(
    portfolio_id: int,
    rate_change_percent: float,
) -> dict:
    """
    Simulate the portfolio impact of an interest-rate change.

    Use this tool for what-if and stress-test questions.

    Args:
        portfolio_id: Portfolio to analyze.
        rate_change_percent: Interest-rate shock in percentage points.

    Returns:
        Scenario assumptions and estimated portfolio impact.
    """

    # Phase 3 starter implementation.
    # Replace with factor-based pricing logic later.

    return {
        "portfolio_id": portfolio_id,
        "scenario": "interest_rate_shock",
        "rate_change_percent": rate_change_percent,
        "status": "simulation_completed",
    }
