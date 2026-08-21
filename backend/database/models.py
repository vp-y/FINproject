from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, JSON
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):

    __tablename__="users"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String
    )


class Portfolio(Base):

    __tablename__="portfolios"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


class Holding(Base):

    __tablename__="holdings"

    id = Column(
        Integer,
        primary_key=True
    )

    portfolio_id = Column(
        Integer,
        ForeignKey("portfolios.id")
    )

    ticker = Column(
        String
    )

    quantity = Column(
        Float
    )

    purchase_price = Column(
        Float
    )


class MarketPrice(Base):

    __tablename__="market_prices"

    id = Column(
        Integer,
        primary_key=True
    )

    ticker = Column(
        String
    )

    price = Column(
        Float
    )

    date = Column(
        Date
    )


class RiskMetric(Base):

    __tablename__="risk_metrics"

    id = Column(
        Integer,
        primary_key=True
    )

    portfolio_id = Column(
        Integer
    )

    volatility = Column(
        Float
    )

    var = Column(
        Float
    )

    sharpe = Column(
        Float
    )


class AgentRun(Base):

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    agent_name = Column(String)
    status = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)


class ToolCall(Base):

    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"))
    tool_name = Column(String)
    # structured JSON, not raw strings — and per Step 3.16, callers must
    # never pass secrets/API keys into these fields since they land here
    input = Column(JSON)
    output_summary = Column(String)
    status = Column(String)


class PortfolioRiskSnapshot(Base):

    __tablename__ = (
        "portfolio_risk_snapshots"
    )

    id = Column(
        Integer,
        primary_key=True,
    )

    portfolio_id = Column(
        Integer,
        index=True,
    )

    timestamp = Column(
        DateTime,
        index=True,
    )

    volatility = Column(
        Float
    )

    var_95 = Column(
        Float
    )

    sharpe_ratio = Column(
        Float
    )