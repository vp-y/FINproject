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


class PortfolioProfile(Base):

    __tablename__ = "portfolio_profiles"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), index=True)
    risk_tolerance = Column(String)        # conservative | moderate | aggressive
    investment_horizon = Column(String)    # short | medium | long
    investment_goal = Column(String, nullable=True)
    created_at = Column(DateTime)


class HoldingDocument(Base):

    __tablename__ = "holding_documents"

    id = Column(Integer, primary_key=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), index=True)
    # denormalized alongside holding_id so status polling by portfolio
    # doesn't need a join through holdings
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), index=True)
    ticker = Column(String)
    company_name = Column(String, nullable=True)
    # pending | fetching | indexing | indexed | failed | no_filing_found
    status = Column(String)
    document_path = Column(String, nullable=True)
    chunk_count = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    updated_at = Column(DateTime)


class PortfolioRecommendation(Base):

    __tablename__ = "portfolio_recommendations"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), index=True)
    session_id = Column(String, nullable=True, index=True)
    generated_at = Column(DateTime, index=True)
    status = Column(String)   # completed | failed
    summary = Column(String)  # synthesis_agent's narrative
    payload = Column(JSON)    # full structured recommendation (weaknesses,
                               # holding_actions, alternatives, metrics...)


class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), index=True)
    conversation_id = Column(String, index=True)
    role = Column(String)     # user | assistant
    content = Column(String)
    created_at = Column(DateTime, index=True)