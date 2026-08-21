import asyncio
import uuid
from datetime import datetime, timezone

from google.genai import types
from google.adk.runners import InMemoryRunner

from schemas.agent import AgentTask
from database.connection import SessionLocal
from database.models import AgentRun, ToolCall
from services.event_emitter import emit_event

from agents.portfolio_agent import portfolio_agent
from agents.risk_agent import risk_agent
from agents.research_agent import research_agent
from agents.scenario_agent import scenario_agent
from agents.synthesis_agent import synthesis_agent

from tools.portfolio_tools import get_portfolio_holdings
from tools.risk_tools import analyze_portfolio_risk, analyze_risk_contribution
from tools.market_tools import analyze_recent_market_move
from services.risk_snapshot_service import save_risk_snapshot, get_previous_snapshot
from analytics.risk_change import compare_risk_snapshots
from external.evidence_merger import build_evidence_items
from external.evidence_ranker import rank_evidence
from data_pipeline.company_mapper import get_company_details

AGENTS = {
    "portfolio": portfolio_agent,
    "risk": risk_agent,
    "research": research_agent,
    "scenario": scenario_agent,
}


def route_request(task):

    if task.task_type == "portfolio":
        return ["portfolio"]

    if task.task_type == "risk":
        return ["portfolio", "risk"]

    if task.task_type == "research":
        return ["research"]

    if task.task_type == "scenario":
        return ["portfolio", "scenario"]

    return [
        "portfolio",
        "risk",
        "research",
    ]


async def run_agent_with_retry(
    agent, query, session_id, trace=None, attempts=3, pause_seconds=8
):
    """ADK/LiteLLM swallow rate-limit errors from the underlying provider
    internally (they log 'Node execution failed' but don't raise up to
    this caller) — the practical signal that a call silently failed is
    getting no final text back. Retry on that signal rather than trusting
    a clean-looking exit."""

    text, tool_results = None, []

    for attempt in range(1, attempts + 1):

        text, tool_results = await run_agent(agent, query, session_id, trace)

        if text is not None or attempt == attempts:
            return text, tool_results

        print(f"    {agent.name} returned no output (likely rate-limited), "
              f"waiting {pause_seconds}s and retrying "
              f"(attempt {attempt}/{attempts})...")
        await asyncio.sleep(pause_seconds)

    return text, tool_results


async def run_agent(agent, query, session_id, trace=None):
    """Runs a single ADK agent once and returns its final text plus the
    structured results of every tool it called (not just its prose
    answer) — the structured data is what downstream synthesis and the
    API response use, since it's exact, not an LLM's paraphrase of it.
    Emits tool_started/tool_completed WebSocket events as they happen."""

    runner = InMemoryRunner(agent=agent)

    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="orchestrator"
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )

    tool_results = []
    pending_call_args = None
    final_text = None

    async for event in runner.run_async(
        user_id="orchestrator",
        session_id=session.id,
        new_message=message
    ):
        if not event.content or not event.content.parts:
            continue

        for part in event.content.parts:

            if part.function_call:

                pending_call_args = dict(part.function_call.args)

                if trace is not None:
                    trace.append({
                        "type": "tool_called",
                        "agent": agent.name,
                        "tool": part.function_call.name
                    })

                await emit_event(session_id, {
                    "type": "tool_started",
                    "agent": agent.name,
                    "tool": part.function_call.name,
                    "message": f"Calling {part.function_call.name}",
                    "data": pending_call_args
                })

            if part.function_response:

                tool_results.append({
                    "tool": part.function_response.name,
                    "args": pending_call_args,
                    "result": part.function_response.response
                })

                await emit_event(session_id, {
                    "type": "tool_completed",
                    "agent": agent.name,
                    "tool": part.function_response.name,
                    "message": f"{part.function_response.name} completed",
                    "data": part.function_response.response
                })

                pending_call_args = None

            if part.text:
                final_text = part.text

    return final_text, tool_results


def persist_agent_run(session_id, agent_name, tool_results, status, started_at):
    """Step 3.16 — records what each agent run actually did. Only
    structured tool args/output summaries are stored, never raw
    secrets/API keys."""

    db = SessionLocal()

    try:
        run = AgentRun(
            session_id=session_id,
            agent_name=agent_name,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(run)
        db.flush()

        for tool_result in tool_results:
            db.add(ToolCall(
                agent_run_id=run.id,
                tool_name=tool_result["tool"],
                input=tool_result.get("args"),
                output_summary=str(tool_result["result"])[:1000],
                status="completed"
            ))

        db.commit()

    finally:
        db.close()


def build_query(task, agent_name):

    if task.portfolio_id is not None:
        return f"{task.user_query} (portfolio_id={task.portfolio_id})"

    return task.user_query


def extract_risk_metrics(evidence):

    for tool_result in evidence.get("risk", {}).get("tool_results", []):

        result = tool_result["result"]

        if "annualized_volatility" in result:
            return {
                "volatility": result.get("annualized_volatility"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "var_95": result.get("historical_var_95"),
            }

    return None


def extract_main_drivers(evidence):

    drivers = []

    for tool_result in evidence.get("risk", {}).get("tool_results", []):

        weights = tool_result["result"].get("weights")

        if not weights:
            continue

        for ticker, weight in sorted(
            weights.items(), key=lambda kv: kv[1], reverse=True
        ):
            if weight >= 0.4:
                drivers.append(
                    f"{ticker} concentration ({weight * 100:.0f}% of portfolio)"
                )

    for tool_result in evidence.get("portfolio", {}).get("tool_results", []):

        holdings = tool_result["result"].get("holdings")

        if holdings and len(holdings) == 1:
            drivers.append(
                f"Single holding exposure ({holdings[0]['ticker']})"
            )

    return drivers


def extract_sources(evidence):

    sources = []

    for tool_result in evidence.get("research", {}).get("tool_results", []):

        for chunk in tool_result["result"].get("results", []):

            metadata = chunk.get("metadata", {})

            sources.append({
                "company": metadata.get("company"),
                "document": metadata.get("document_name"),
                "page": metadata.get("page_number"),
            })

    return sources


async def synthesize_summary(user_query, evidence, session_id):

    evidence_text = "\n\n".join(
        f"--- {name} agent ---\n"
        f"Summary: {data['summary']}\n"
        f"Tool results: {[tr['result'] for tr in data['tool_results']]}"
        for name, data in evidence.items()
    )

    prompt = f"""
User question: {user_query}

Evidence gathered by specialist agents:

{evidence_text}

Write a clear, concise synthesis answering the user's question using
only the evidence above.
"""

    text, _ = await run_agent_with_retry(synthesis_agent, prompt, session_id)

    return text


async def run_orchestration(task: AgentTask, session_id: str = None):
    """The Phase 3+4 end-to-end flow:
    route -> run specialist agents -> synthesize -> respond with sources,
    emitting WebSocket events throughout for whichever connection opened
    this session_id (if any — a session_id-less caller, e.g. a script or
    test, still works, it just has no live listener)."""

    session_id = session_id or str(uuid.uuid4())

    # Step 5.13's flagship workflow (snapshot comparison, risk
    # contribution, ranked internal+market+external evidence) is a
    # strict upgrade of the plain "risk" path — route there instead of
    # the generic per-agent loop whenever there's a portfolio to explain.
    if task.task_type == "risk" and task.portfolio_id is not None:
        return await run_risk_explanation_workflow(
            task.portfolio_id, task.user_query, session_id
        )

    trace = []

    agent_names = route_request(task)

    trace.append({
        "type": "supervisor_routed",
        "task_type": task.task_type,
        "agents": agent_names
    })

    await emit_event(session_id, {
        "type": "agent_started",
        "agent": "supervisor",
        "message": f"Identified {task.task_type} analysis",
        "data": {"agents": agent_names}
    })
    await emit_event(session_id, {
        "type": "agent_completed",
        "agent": "supervisor",
        "message": f"Routed to: {', '.join(agent_names)}"
    })

    evidence = {}

    for name in agent_names:

        agent = AGENTS[name]

        trace.append({"type": "agent_started", "agent": name})
        started_at = datetime.now(timezone.utc)

        await emit_event(session_id, {
            "type": "agent_started",
            "agent": agent.name,
            "message": f"{agent.name} starting"
        })

        query = build_query(task, name)

        try:
            text, tool_results = await run_agent_with_retry(
                agent, query, session_id, trace
            )
        except Exception as e:
            # One agent failing (e.g. the LLM provider's rate limit
            # exhausting all retries) shouldn't crash the whole request —
            # degrade gracefully: record the failure, tell the live
            # listener, and let the remaining agents still run.
            text, tool_results = None, []

            trace.append({
                "type": "error", "agent": name, "error": str(e)
            })

            await emit_event(session_id, {
                "type": "error",
                "agent": agent.name,
                "message": f"{agent.name} failed: {e.__class__.__name__}",
                "data": {"error": str(e)}
            })

        evidence[name] = {
            "summary": text,
            "tool_results": tool_results
        }

        trace.append({"type": "agent_completed", "agent": name})

        await emit_event(session_id, {
            "type": "agent_completed",
            "agent": agent.name,
            "message": f"{agent.name} completed",
            "data": {"tool_results": tool_results}
        })

        persist_agent_run(
            session_id,
            agent.name,
            tool_results,
            status="completed" if text is not None else "failed",
            started_at=started_at
        )

    trace.append({"type": "agent_started", "agent": "synthesis_agent"})
    synthesis_started_at = datetime.now(timezone.utc)

    await emit_event(session_id, {
        "type": "agent_started",
        "agent": "synthesis_agent",
        "message": "Generating final intelligence report..."
    })

    try:
        summary = await synthesize_summary(task.user_query, evidence, session_id)
    except Exception as e:
        summary = None
        trace.append({"type": "error", "agent": "synthesis_agent", "error": str(e)})
        await emit_event(session_id, {
            "type": "error",
            "agent": "synthesis_agent",
            "message": f"synthesis_agent failed: {e.__class__.__name__}",
            "data": {"error": str(e)}
        })

    trace.append({"type": "agent_completed", "agent": "synthesis_agent"})

    await emit_event(session_id, {
        "type": "agent_completed",
        "agent": "synthesis_agent",
        "message": "Synthesis complete"
    })

    persist_agent_run(
        session_id,
        "synthesis_agent",
        [],
        status="completed" if summary is not None else "failed",
        started_at=synthesis_started_at
    )

    # Consistent with run_risk_explanation_workflow's Step 5.18 shape,
    # so the frontend gets one predictable response regardless of which
    # path handled the request — this path just doesn't populate
    # risk_change/major_contributors, since snapshot comparison and
    # contribution analysis are specific to the risk workflow.
    all_tool_results = [
        tr for data in evidence.values() for tr in data["tool_results"]
    ]

    ranked_evidence = rank_evidence(build_evidence_items(all_tool_results))

    evidence_bucket = {
        "internal": [
            e for e in ranked_evidence
            if e["source_type"] in ("regulatory_filing", "internal_document")
        ],
        "market": [
            e for e in ranked_evidence if e["source_type"] == "market_data"
        ],
        "external": [
            e for e in ranked_evidence
            if e["source_type"] in ("major_news", "general_news", "company_website")
        ],
    }

    result = {
        "portfolio_id": task.portfolio_id,
        "session_id": session_id,
        "summary": summary,
        "risk_change": None,
        "major_contributors": [],
        "evidence": evidence_bucket,
        "sources": [
            {
                "document": item.get("title"),
                "page": item.get("page"),
                "company": item.get("company"),
            }
            for item in evidence_bucket["internal"]
        ],
        "trace": trace,
    }

    await emit_event(session_id, {
        "type": "final_result",
        "agent": "synthesis_agent",
        "message": "Analysis completed",
        "data": result
    })

    return result


def build_risk_explanation_prompt(
    user_query, current_risk, risk_change, major_contributors, ranked_evidence
):

    if risk_change:
        change_text = (
            f"Volatility changed by {risk_change['volatility_change']:+.4f}, "
            f"VaR changed by {risk_change['var_change']:+.4f}, "
            f"Sharpe changed by {risk_change['sharpe_change']:+.4f} "
            f"since the previous snapshot."
        )
    else:
        change_text = (
            "No previous risk snapshot exists yet — this is the first "
            "recorded snapshot for this portfolio, so no change can be "
            "measured yet."
        )

    contributors_text = "\n".join(
        f"- {c['ticker']}: {c['risk_contribution'] * 100:.1f}% of portfolio risk"
        for c in major_contributors
    ) or "(none)"

    evidence_text = "\n".join(
        f"- [{item['source_type']}, score={item['score']}] {item.get('title')}"
        + (f" (page {item['page']})" if item.get("page") else "")
        for item in ranked_evidence[:10]
    ) or "(no evidence retrieved)"

    return f"""
User question: {user_query}

Current risk metrics: {current_risk}

Risk change since last snapshot: {change_text}

Risk contribution by holding:
{contributors_text}

Ranked evidence (highest-quality/most-relevant first):
{evidence_text}

Write a clear explanation of why portfolio risk changed (or, if no
prior snapshot exists, explain the current risk picture instead).

Rules:
- Do not invent numbers — use only the figures given above.
- Distinguish confirmed structural/regulatory disclosures from recent
  market price movement from external news speculation.
- For anything sourced from external news, use hedged language like
  "may have contributed" — never state it "definitely caused" the
  change unless it's a directly calculated metric given above.
- Cite which evidence supports each claim.
"""


async def run_risk_explanation_workflow(
    portfolio_id: int, user_query: str, session_id: str
):
    """Step 5.13's flagship workflow:
    Portfolio -> Risk -> Snapshot compare -> Contribution -> Market
    context -> Research (RAG + news) -> Evidence ranking -> Synthesis.

    Steps 1-5 call the underlying deterministic tools directly rather
    than routing through an LLM agent call — there is no judgment call
    in "get this portfolio's holdings" or "compute the covariance
    matrix", and Step 5.2 explicitly says to use deterministic data
    first rather than over-relying on the LLM. Only Research (deciding
    what/how to search) and Synthesis (writing the explanation) go
    through a real LLM agent call."""

    trace = []

    async def emit(agent, event_type, message, data=None, tool=None):

        event = {"type": event_type, "agent": agent, "message": message}

        if tool:
            event["tool"] = tool

        if data is not None:
            event["data"] = data

        await emit_event(session_id, event)
        trace.append(event)

    def record(agent_name, tool_results, status="completed"):

        persist_agent_run(
            session_id, agent_name, tool_results,
            status=status, started_at=datetime.now(timezone.utc)
        )

    empty_evidence = {"internal": [], "market": [], "external": []}

    # STEP 1 — Portfolio: get holdings
    await emit("portfolio_agent", "agent_started", "Retrieving portfolio holdings")
    holdings_result = get_portfolio_holdings(portfolio_id)
    await emit(
        "portfolio_agent", "agent_completed",
        f"Retrieved {len(holdings_result.get('holdings', []))} holdings",
        data=holdings_result
    )
    record("portfolio_agent", [{
        "tool": "get_portfolio_holdings",
        "args": {"portfolio_id": portfolio_id},
        "result": holdings_result
    }])

    if not holdings_result.get("holdings"):
        return {
            "portfolio_id": portfolio_id,
            "session_id": session_id,
            "summary": f"No holdings found for portfolio {portfolio_id}.",
            "risk_change": None,
            "major_contributors": [],
            "evidence": empty_evidence,
            "sources": [],
            "trace": trace,
        }

    # STEP 2 — Risk: calculate current risk
    await emit("risk_agent", "agent_started", "Calculating current portfolio risk")
    current_risk = analyze_portfolio_risk(portfolio_id)
    record("risk_agent", [{
        "tool": "analyze_portfolio_risk",
        "args": {"portfolio_id": portfolio_id},
        "result": current_risk
    }])

    if "error" in current_risk:
        await emit("risk_agent", "agent_completed", current_risk["error"])
        return {
            "portfolio_id": portfolio_id,
            "session_id": session_id,
            "summary": current_risk["error"],
            "risk_change": None,
            "major_contributors": [],
            "evidence": empty_evidence,
            "sources": [],
            "trace": trace,
        }

    await emit(
        "risk_agent", "agent_completed",
        "Calculated volatility, VaR, and Sharpe ratio",
        data=current_risk
    )

    # STEP 3 — Risk Comparison: save this snapshot, compare to the
    # previous one (if any exists — see Step 5.14)
    now = datetime.now(timezone.utc)

    new_snapshot = save_risk_snapshot(
        portfolio_id,
        volatility=current_risk["annualized_volatility"],
        var_95=current_risk["historical_var_95"],
        sharpe_ratio=current_risk["sharpe_ratio"],
    )

    previous_snapshot = get_previous_snapshot(portfolio_id, before=now)

    if previous_snapshot:
        risk_change = compare_risk_snapshots(previous_snapshot, new_snapshot)
        change_message = (
            f"Volatility change: {risk_change['volatility_change']:+.4f}, "
            f"VaR change: {risk_change['var_change']:+.4f}"
        )
    else:
        risk_change = None
        change_message = (
            "No previous snapshot exists yet — recorded the first one "
            "for this portfolio."
        )

    await emit("risk_agent", "agent_completed", change_message, data=risk_change)

    # STEP 4 — Contribution Analysis
    await emit(
        "risk_contribution_engine", "agent_started",
        "Analyzing risk contribution by holding"
    )

    contribution_result = analyze_risk_contribution(portfolio_id)
    contributions = contribution_result.get("contribution", {})

    major_contributors = [
        {"ticker": ticker, "risk_contribution": round(pct, 4)}
        for ticker, pct in sorted(
            contributions.items(), key=lambda kv: kv[1], reverse=True
        )
    ]

    top_ticker = major_contributors[0]["ticker"] if major_contributors else None

    record("risk_contribution_engine", [{
        "tool": "analyze_risk_contribution",
        "args": {"portfolio_id": portfolio_id},
        "result": contribution_result
    }])

    await emit(
        "risk_contribution_engine", "agent_completed",
        f"Identified {top_ticker} as the largest risk contributor"
        if top_ticker else "No contribution data available",
        data=major_contributors
    )

    if not top_ticker:
        return {
            "portfolio_id": portfolio_id,
            "session_id": session_id,
            "summary": "Risk metrics calculated, but contribution analysis "
                       "returned no data to investigate further.",
            "risk_change": risk_change,
            "major_contributors": [],
            "evidence": empty_evidence,
            "sources": [],
            "trace": trace,
        }

    # STEP 5 — Market Context for the top contributor
    await emit(
        "market_context", "tool_started",
        f"Checking recent price movement for {top_ticker}",
        tool="analyze_recent_market_move"
    )

    market_move = analyze_recent_market_move(top_ticker)

    await emit(
        "market_context", "tool_completed",
        f"{top_ticker} moved {market_move.get('change_percent', 0):.2f}% "
        f"over the last {market_move.get('period', 'N/A')}",
        data=market_move,
        tool="analyze_recent_market_move"
    )
    record("market_context", [{
        "tool": "analyze_recent_market_move",
        "args": {"ticker": top_ticker},
        "result": market_move
    }])

    # STEP 6 — Research Agent: internal docs + recent news, via the
    # real LLM agent (this is the one step that needs judgment)
    company_info = get_company_details(top_ticker)
    company_name = company_info.get("name") or top_ticker

    await emit(
        "research_agent", "agent_started",
        f"Searching internal filings and recent news for {company_name}"
    )

    research_query = (
        f"Investigate recent risk factors and news for {company_name} "
        f"({top_ticker}) that could explain increased portfolio risk."
    )

    try:
        research_text, research_tool_results = await run_agent_with_retry(
            research_agent, research_query, session_id, trace
        )
    except Exception as e:
        research_text, research_tool_results = None, []
        await emit(
            "research_agent", "error",
            f"research_agent failed: {e.__class__.__name__}",
            data={"error": str(e)}
        )

    record(
        "research_agent", research_tool_results,
        status="completed" if research_text is not None else "failed"
    )

    await emit(
        "research_agent", "agent_completed",
        "Research complete",
        data={"tool_results_count": len(research_tool_results)}
    )

    # STEP 7 — Evidence Ranker
    await emit("evidence_ranker", "agent_started", "Ranking gathered evidence")

    raw_items = build_evidence_items(research_tool_results)

    # the Step 5 market-move call went through analyze_recent_market_move
    # directly, not via the research agent, so fold it in here too
    raw_items.extend(build_evidence_items([{
        "tool": "analyze_recent_market_move",
        "result": market_move
    }]))

    ranked_evidence = rank_evidence(raw_items)

    evidence_bucket = {
        "internal": [
            e for e in ranked_evidence
            if e["source_type"] in ("regulatory_filing", "internal_document")
        ],
        "market": [
            e for e in ranked_evidence if e["source_type"] == "market_data"
        ],
        "external": [
            e for e in ranked_evidence
            if e["source_type"] in ("major_news", "general_news", "company_website")
        ],
    }

    await emit(
        "evidence_ranker", "agent_completed",
        f"Ranked {len(ranked_evidence)} evidence sources",
        data={"count": len(ranked_evidence)}
    )

    # STEP 8 — Synthesis Agent
    await emit(
        "synthesis_agent", "agent_started",
        "Generating final intelligence report..."
    )

    synthesis_prompt = build_risk_explanation_prompt(
        user_query, current_risk, risk_change, major_contributors, ranked_evidence
    )

    try:
        summary, _ = await run_agent_with_retry(
            synthesis_agent, synthesis_prompt, session_id
        )
    except Exception as e:
        summary = None
        await emit(
            "synthesis_agent", "error",
            f"synthesis_agent failed: {e.__class__.__name__}",
            data={"error": str(e)}
        )

    record(
        "synthesis_agent", [],
        status="completed" if summary is not None else "failed"
    )

    await emit("synthesis_agent", "agent_completed", "Synthesis complete")

    sources = [
        {
            "document": item.get("title"),
            "page": item.get("page"),
            "company": item.get("company"),
        }
        for item in evidence_bucket["internal"]
    ]

    result = {
        "portfolio_id": portfolio_id,
        "session_id": session_id,
        "summary": summary,
        "risk_change": risk_change,
        "major_contributors": major_contributors,
        "evidence": evidence_bucket,
        "sources": sources,
        "trace": trace,
    }

    await emit_event(session_id, {
        "type": "final_result",
        "agent": "synthesis_agent",
        "message": "Analysis completed",
        "data": result
    })

    return result
