"use client";

import { Card, SectionTitle, EmptyState, Badge } from "@/components/ui";
import Sparkline from "@/components/Sparkline";
import { deltaTone, formatSignedNumber, formatSignedPercent } from "@/lib/format";
import type { ExpectedImpact, HoldingAction, Horizon } from "@/lib/types";

const VERDICT_TONE: Record<string, "critical" | "warning" | "neutral" | "good"> = {
  sell: "critical",
  reduce: "warning",
  hold: "neutral",
  increase: "good",
};

const VERDICT_ICON: Record<string, string> = {
  sell: "✕",
  reduce: "▼",
  hold: "●",
  increase: "▲",
};

const VERDICT_ORDER: HoldingAction["verdict"][] = ["sell", "reduce", "increase", "hold"];

const VERDICT_LABEL: Record<string, string> = {
  sell: "Sell",
  reduce: "Reduce",
  increase: "Increase",
  hold: "Hold",
};

const IMPACT_TONE_TEXT: Record<string, string> = {
  good: "text-[var(--good)]",
  warning: "text-[var(--warning)]",
  critical: "text-[var(--critical)]",
  neutral: "text-[var(--ink-3)]",
};

function ImpactRow({ impact }: { impact: ExpectedImpact }) {

  const rows: { label: string; value: number | null; invert: boolean; format: (v: number) => string }[] = [
    { label: "Volatility", value: impact.volatility_delta, invert: true, format: (v) => formatSignedPercent(v) },
    { label: "Sharpe", value: impact.sharpe_delta, invert: false, format: (v) => formatSignedNumber(v, 2) },
    { label: "VaR (95%)", value: impact.var_delta, invert: false, format: (v) => formatSignedPercent(v) },
    { label: "Concentration", value: impact.hhi_delta, invert: true, format: (v) => formatSignedNumber(v, 3) },
  ];

  const known = rows.filter((row) => row.value != null);

  if (known.length === 0) {
    return null;
  }

  return (

    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 border-t border-[var(--gridline)] pt-2 text-xs">

      {

        known.map((row) => (

          <span
            key={row.label}
            className={IMPACT_TONE_TEXT[deltaTone(row.value as number, row.invert)]}
          >
            {row.label}: {row.format(row.value as number)}
          </span>

        ))

      }

    </div>

  );
}

function ActionCard({ action }: { action: HoldingAction }) {

  const tone = VERDICT_TONE[action.verdict];
  const isPositive = (action.change_percent ?? 0) >= 0;

  return (

    <li className="rounded-lg border border-[var(--border)] p-3">

      <div className="flex items-start justify-between gap-2">

        <div className="flex items-center gap-2">
          <span
            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
              tone === "good" ? "bg-[var(--good-soft)] text-[var(--good)]" :
              tone === "warning" ? "bg-[var(--warning-soft)] text-[var(--warning)]" :
              tone === "critical" ? "bg-[var(--critical-soft)] text-[var(--critical)]" :
              "bg-[var(--accent-soft)] text-[var(--accent)]"
            }`}
            aria-hidden="true"
          >
            {VERDICT_ICON[action.verdict]}
          </span>
          <span className="text-sm font-medium">{action.ticker}</span>
        </div>

        <Badge tone={tone}>
          {(action.weight * 100).toFixed(0)}% of portfolio
        </Badge>

      </div>

      {
        action.sparkline && action.sparkline.length > 1 && (
          <div className="mt-2 flex items-center gap-3">
            <div className="flex-1">
              <Sparkline values={action.sparkline} positive={isPositive} />
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold tabular-nums">
                {action.current_price != null ? `$${action.current_price.toFixed(2)}` : "—"}
              </p>
              {
                action.change_percent != null && (
                  <p className={`text-xs tabular-nums ${isPositive ? "text-[var(--good)]" : "text-[var(--critical)]"}`}>
                    {isPositive ? "▲" : "▼"} {formatSignedPercent(action.change_percent / 100)}
                  </p>
                )
              }
            </div>
          </div>
        )
      }

      <ul className="mt-2 space-y-0.5">
        {
          action.reasoning.map((reason, index) => (
            <li key={index} className="text-sm text-[var(--ink-2)]">{reason}</li>
          ))
        }
      </ul>

      {/* A "hold" verdict applies no hypothetical reweighting, so its
          impact is always exactly zero across the board — showing that
          all-zero row adds noise, not information. */}
      {action.verdict !== "hold" && <ImpactRow impact={action.expected_impact} />}

    </li>

  );
}

export default function RecommendedActionsPanel({
  actions,
  horizonFilter,
}: {
  actions: HoldingAction[];
  horizonFilter: "all" | Horizon;
}) {

  const filtered = actions.filter(
    (action) => horizonFilter === "all" || action.horizon === horizonFilter
  );

  const grouped = VERDICT_ORDER.map((verdict) => ({
    verdict,
    items: filtered.filter((action) => action.verdict === verdict),
  })).filter((group) => group.items.length > 0);

  return (

    <Card>

      <SectionTitle count={filtered.length}>
        Recommended Actions
      </SectionTitle>

      {

        grouped.length === 0 ? (

          <EmptyState>
            No holding actions for this horizon.
          </EmptyState>

        ) : (

          <div className="space-y-5 px-5 pb-5 pt-2">

            {

              grouped.map((group) => (

                <div key={group.verdict}>

                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
                    {VERDICT_LABEL[group.verdict]}
                  </h3>

                  <ul className="space-y-3">
                    {
                      group.items.map((action) => (
                        <ActionCard key={action.ticker} action={action} />
                      ))
                    }
                  </ul>

                </div>

              ))

            }

          </div>

        )

      }

    </Card>

  );
}
