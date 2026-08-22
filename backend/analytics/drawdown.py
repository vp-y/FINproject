def calculate_max_drawdown(returns) -> dict:
    """Largest peak-to-trough decline in a cumulative-wealth series built
    from a daily-returns series. Returns a negative fraction (e.g. -0.23
    = a 23% drawdown from the prior peak) and the date it bottomed out.

    Args:
        returns: pandas Series of daily returns, indexed by date.

    Returns:
        {"max_drawdown": float, "trough_date": str | None}
    """

    if returns is None or len(returns) == 0:
        return {"max_drawdown": 0.0, "trough_date": None}

    wealth_index = (1 + returns).cumprod()
    running_max = wealth_index.cummax()
    drawdown = wealth_index / running_max - 1

    max_drawdown = float(drawdown.min())
    trough_date = drawdown.idxmin()

    return {
        "max_drawdown": max_drawdown,
        "trough_date": trough_date.isoformat() if hasattr(trough_date, "isoformat") else str(trough_date),
    }
