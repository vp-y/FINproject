"use client";

import { Card, SectionTitle, EmptyState } from "@/components/ui";
import { deltaTone, formatSignedNumber } from "@/lib/format";
import type { MetricsComparisonRow } from "@/lib/types";

const TONE_TEXT: Record<string, string> = {
  good: "text-[var(--good)]",
  warning: "text-[var(--warning)]",
  critical: "text-[var(--critical)]",
  neutral: "text-[var(--ink-2)]",
};

const PERCENT_METRICS = new Set(["volatility", "var_95", "top_sector_weight", "max_drawdown"]);

function formatValue(metric: string, value: number): string {
  if (PERCENT_METRICS.has(metric)) {
    return `${(value * 100).toFixed(1)}%`;
  }
  return value.toFixed(2);
}

export default function MetricsComparisonTable({
  rows,
}: {
  rows: MetricsComparisonRow[];
}) {

  return (

    <Card>

      <SectionTitle>
        Current vs. Recommended
      </SectionTitle>

      {

        rows.length === 0 ? (

          <EmptyState>
            Not enough data to compare states yet.
          </EmptyState>

        ) : (

          <div className="overflow-x-auto px-5 pb-5 pt-2">

            <table className="w-full text-sm">

              <thead>
                <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--ink-3)]">
                  <th className="py-2 pr-3 font-medium">Metric</th>
                  <th className="py-2 pr-3 text-right font-medium">Current</th>
                  <th className="py-2 pr-3 text-right font-medium">Recommended</th>
                  <th className="py-2 text-right font-medium">Change</th>
                </tr>
              </thead>

              <tbody>

                {

                  rows.map((row) => (

                    <tr
                      key={row.metric}
                      className="border-b border-[var(--gridline)] last:border-0"
                    >
                      <td className="py-2 pr-3">{row.label}</td>
                      <td className="py-2 pr-3 text-right tabular-nums">
                        {formatValue(row.metric, row.current)}
                      </td>
                      <td className="py-2 pr-3 text-right tabular-nums">
                        {formatValue(row.metric, row.recommended)}
                      </td>
                      <td className={`py-2 text-right tabular-nums ${TONE_TEXT[deltaTone(row.delta, row.invert)]}`}>
                        {row.delta > 0 ? "▲ " : row.delta < 0 ? "▼ " : ""}
                        {formatSignedNumber(row.delta, 3)}
                      </td>
                    </tr>

                  ))

                }

              </tbody>

            </table>

          </div>

        )

      }

    </Card>

  );
}
