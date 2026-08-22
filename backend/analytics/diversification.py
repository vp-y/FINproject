def calculate_herfindahl_index(weights: dict) -> float:
    """Herfindahl-Hirschman Index over position weights — sum of squared
    weights. Ranges from ~1/n (perfectly even across n positions) to 1.0
    (a single holding). Higher = more concentrated."""

    return sum(weight ** 2 for weight in weights.values())


def effective_number_of_positions(hhi: float) -> float:
    """1/HHI — the "effective" number of equally-weighted positions a
    portfolio behaves like. A 10-holding portfolio with one dominant 60%
    position has an effective count much closer to 2 than to 10."""

    return 1 / hhi if hhi else 0.0
