"use client";

import { Card, SectionTitle, StatTile } from "@/components/ui";
import type { PortfolioMetricsBundle } from "@/lib/types";

function pct(value: number | null | undefined, digits = 1): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

function num(value: number | null | undefined, digits = 2): string {
  if (value == null) return "—";
  return value.toFixed(digits);
}

export default function PortfolioMetricsGrid({
  metrics,
}: {
  metrics: PortfolioMetricsBundle | null;
}) {

  if (!metrics) {
    return null;
  }

  return (

    <Card>

      <SectionTitle>
        Portfolio Metrics
      </SectionTitle>

      <div className="grid grid-cols-2 gap-3 px-5 pb-5 pt-2 sm:grid-cols-4">

        <StatTile icon="📈" label="Exp. Return" value={pct(metrics.benchmark?.portfolio_annual_return)} tone="good" />
        <StatTile icon="📉" label="Volatility" value={pct(metrics.volatility)} tone="warning" />
        <StatTile icon="⚖️" label="Sharpe Ratio" value={num(metrics.sharpe_ratio)} />
        <StatTile icon="🛡️" label="VaR (95%)" value={pct(metrics.var_95)} tone="critical" />
        <StatTile icon="↘️" label="Drawdown" value={pct(metrics.max_drawdown)} tone="critical" />
        <StatTile icon="🧩" label="Positions" value={num(metrics.effective_number_of_positions, 1)} />
        <StatTile icon="🏭" label="Top Sector" value={pct(metrics.top_sector_weight, 0)} tone="warning" />
        <StatTile icon="🔗" label="Correlation" value={num(metrics.average_pairwise_correlation)} />
        <StatTile icon="β" label="Beta" value={num(metrics.benchmark?.beta)} />
        <StatTile icon="α" label="Alpha" value={pct(metrics.benchmark?.alpha)} tone="good" />

      </div>

    </Card>

  );
}
