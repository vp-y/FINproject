def calculate_correlation_matrix(returns_df) -> dict:
    """Pairwise Pearson correlation of each ticker's daily returns.
    JSON-safe nested dict: {ticker: {ticker: correlation}}."""

    return returns_df.corr().round(4).to_dict()


def average_pairwise_correlation(returns_df) -> float:
    """Mean of the off-diagonal correlation matrix entries — a single
    number summarizing how much real diversification benefit the
    portfolio's holdings give each other (near 1.0 = they all move
    together despite being "different" positions; near 0 = genuinely
    diversified)."""

    matrix = returns_df.corr().values
    n = matrix.shape[0]

    if n < 2:
        return 0.0

    # n ones sit on the diagonal; every other cell is an off-diagonal
    # pairwise correlation, each pair counted twice (i,j) and (j,i).
    off_diagonal_sum = matrix.sum() - n
    pair_count = n * (n - 1)

    return float(off_diagonal_sum / pair_count) if pair_count else 0.0
