"use client";

import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAgentWebSocket } from "@/hooks/useAgentWebSocket";
import { Card } from "@/components/ui";
import AgentMonitor from "@/components/AgentMonitor";
import ChatPanel from "@/components/ChatPanel";
import PortfolioMetricsGrid from "@/components/PortfolioMetricsGrid";
import SectorAllocationChart from "@/components/SectorAllocationChart";
import WeaknessesPanel from "@/components/WeaknessesPanel";
import RecommendedActionsPanel from "@/components/RecommendedActionsPanel";
import AlternativesPanel from "@/components/AlternativesPanel";
import MetricsComparisonTable from "@/components/MetricsComparisonTable";
import { formatSignedPercent } from "@/lib/format";
import type { Horizon, PortfolioDetail, RecommendationPayload } from "@/lib/types";

type HorizonFilter = "all" | Horizon;

const HORIZON_OPTIONS: { value: HorizonFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "short_term", label: "Short-term" },
  { value: "long_term", label: "Long-term" },
];

export default function DashboardPage({
  params,
}: {
  params: Promise<{ portfolioId: string }>;
}) {

  const { portfolioId } = use(params);
  const id = Number(portfolioId);

  const { events, connected, sessionId } = useAgentWebSocket();

  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationPayload | null>(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [horizonFilter, setHorizonFilter] = useState<HorizonFilter>("all");

  useEffect(() => {

    api.get<PortfolioDetail>(`/portfolio/${id}`)
      .then((response) => setPortfolio(response.data))
      .catch(() => {});

  }, [id]);

  useEffect(() => {

    api.get(`/recommendations/${id}/latest`)
      .then((response) => {
        if (response.data.status === "found") {
          setRecommendation(response.data);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingRecommendation(false));

  }, [id]);

  const generate = () => {

    setGenerating(true);

    api.post(`/recommendations/${id}/generate`, null, { params: { session_id: sessionId } })
      .then((response) => setRecommendation(response.data))
      .catch(() => {})
      .finally(() => setGenerating(false));

  };

  return (

    <div className="min-h-screen">

      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              {portfolio?.name ?? "Portfolio"}
            </h1>
            <p className="text-sm text-[var(--ink-2)]">
              Recommendation dashboard
            </p>
          </div>

          <span className="flex items-center gap-2 text-xs font-medium text-[var(--ink-2)]">
            <span className={`h-2 w-2 rounded-full ${connected ? "bg-[var(--good)]" : "bg-[var(--ink-3)]"}`} />
            {connected ? "Live" : "Offline"}
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">

        <div className="space-y-6">

          {

            recommendation?.current_metrics?.total_value != null && (

              <Card className="p-5">

                <p className="text-xs text-[var(--ink-3)]">
                  Total Portfolio Value
                </p>

                <p className="mt-1 text-3xl font-semibold tabular-nums">
                  ${recommendation.current_metrics.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>

                {

                  recommendation.current_metrics.benchmark?.portfolio_annual_return != null && (

                    <p
                      className={`mt-1 text-sm font-medium tabular-nums ${
                        recommendation.current_metrics.benchmark.portfolio_annual_return >= 0
                          ? "text-[var(--good)]"
                          : "text-[var(--critical)]"
                      }`}
                    >
                      {
                        recommendation.current_metrics.benchmark.portfolio_annual_return >= 0 ? "▲" : "▼"
                      }{" "}
                      {formatSignedPercent(recommendation.current_metrics.benchmark.portfolio_annual_return)}{" "}
                      <span className="font-normal text-[var(--ink-3)]">annualized return</span>
                    </p>

                  )

                }

              </Card>

            )

          }

          <Card className="p-5">

            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
              Holdings
            </h2>

            {

              portfolio?.holdings.length ? (

                <ul className="space-y-1 text-sm">
                  {
                    portfolio.holdings.map((holding) => (
                      <li key={holding.id} className="flex justify-between">
                        <span>{holding.ticker}</span>
                        <span className="text-[var(--ink-3)]">{holding.quantity} sh</span>
                      </li>
                    ))
                  }
                </ul>

              ) : (

                <p className="text-sm text-[var(--ink-3)]">
                  No holdings.
                </p>

              )

            }

          </Card>

          <ChatPanel portfolioId={id} />

        </div>

        <div className="space-y-6">

          {

            !recommendation && !loadingRecommendation && (

              <Card className="p-5 text-center">

                <p className="mb-4 text-sm text-[var(--ink-2)]">
                  No recommendation generated yet.
                </p>

                <button
                  onClick={generate}
                  disabled={generating || !connected}
                  className="rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-[var(--accent-ink)] transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {generating ? "Analyzing..." : "Generate Recommendation"}
                </button>

              </Card>

            )

          }

          {
            generating && (
              <AgentMonitor events={events} connected={connected} />
            )
          }

          {

            recommendation && (

              <>

                <Card className="p-5">

                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
                      Summary
                    </h2>
                    <button
                      onClick={generate}
                      disabled={generating || !connected}
                      className="text-xs font-medium text-[var(--accent)] hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {generating ? "Regenerating..." : "Regenerate"}
                    </button>
                  </div>

                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--ink)]">
                    {recommendation.summary ?? "No summary generated."}
                  </p>

                </Card>

                <PortfolioMetricsGrid metrics={recommendation.current_metrics} />

                {
                  recommendation.current_metrics?.sector_weights && (
                    <SectorAllocationChart sectorWeights={recommendation.current_metrics.sector_weights} />
                  )
                }

                <WeaknessesPanel weaknesses={recommendation.weaknesses} />

                <div className="flex gap-2">
                  {
                    HORIZON_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setHorizonFilter(option.value)}
                        className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                          horizonFilter === option.value
                            ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)]"
                            : "border-[var(--border)] text-[var(--ink-2)]"
                        }`}
                      >
                        {option.label}
                      </button>
                    ))
                  }
                </div>

                <RecommendedActionsPanel
                  actions={recommendation.holding_actions}
                  horizonFilter={horizonFilter}
                />

                <AlternativesPanel
                  alternatives={recommendation.alternatives}
                  diversificationSuggestions={recommendation.diversification_suggestions}
                  horizonFilter={horizonFilter}
                />

                <MetricsComparisonTable rows={recommendation.metrics_comparison} />

              </>

            )

          }

        </div>

      </main>

    </div>

  );

}
