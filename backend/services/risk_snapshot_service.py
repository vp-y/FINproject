from datetime import datetime, timezone

from database.connection import SessionLocal
from database.models import PortfolioRiskSnapshot


def save_risk_snapshot(
    portfolio_id: int,
    volatility: float,
    var_95: float,
    sharpe_ratio: float,
):

    db = SessionLocal()

    try:
        snapshot = PortfolioRiskSnapshot(
            portfolio_id=portfolio_id,
            timestamp=datetime.now(timezone.utc),
            volatility=volatility,
            var_95=var_95,
            sharpe_ratio=sharpe_ratio,
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "id": snapshot.id,
            "portfolio_id": snapshot.portfolio_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "volatility": snapshot.volatility,
            "var_95": snapshot.var_95,
            "sharpe_ratio": snapshot.sharpe_ratio,
        }

    finally:
        db.close()


def get_previous_snapshot(portfolio_id: int, before: datetime):
    """The most recent snapshot strictly before `before` — pass the
    timestamp of the snapshot just saved, so comparing doesn't just
    compare a snapshot against itself."""

    db = SessionLocal()

    try:
        snapshot = (
            db.query(PortfolioRiskSnapshot)
            .filter(
                PortfolioRiskSnapshot.portfolio_id == portfolio_id,
                PortfolioRiskSnapshot.timestamp < before,
            )
            .order_by(PortfolioRiskSnapshot.timestamp.desc())
            .first()
        )

        if not snapshot:
            return None

        return {
            "id": snapshot.id,
            "portfolio_id": snapshot.portfolio_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "volatility": snapshot.volatility,
            "var_95": snapshot.var_95,
            "sharpe_ratio": snapshot.sharpe_ratio,
        }

    finally:
        db.close()
