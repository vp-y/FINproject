def compare_risk_snapshots(
    previous: dict,
    current: dict,
) -> dict:

    return {

        "volatility_change":
            current["volatility"]
            - previous["volatility"],

        "var_change":
            current["var_95"]
            - previous["var_95"],

        "sharpe_change":
            current["sharpe_ratio"]
            - previous["sharpe_ratio"],
    }
