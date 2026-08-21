"use client";

import type { Evidence } from "@/components/EvidencePanel";
import { deltaTone, formatSignedNumber, formatSignedPercent, type Tone } from "@/lib/format";
import { Card, EmptyState } from "@/components/ui";

export type AnalyzeResponse = {
  portfolio_id: number | null;
  session_id: string;
  summary: string | null;
  risk_change: {
    volatility_change: number;
    var_change: number;
    sharpe_change: number;
  } | null;
  major_contributors: {
    ticker: string;
    risk_contribution: number;
  }[];
  evidence: Evidence;
  sources: {
    company?: string;
    document?: string;
    page?: number;
  }[];
};

const toneText: Record<Tone, string> = {
  good: "text-[var(--good)]",
  warning: "text-[var(--warning)]",
  critical: "text-[var(--critical)]",
  neutral: "text-[var(--ink)]",
};

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: Tone;
}) {

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-4 py-3">
      <p className="text-xs text-[var(--ink-3)]">
        {label}
      </p>
      <p className={`text-lg font-semibold tabular-nums ${toneText[tone]}`}>
        {value}
      </p>
    </div>
  );
}

export default function AnalysisResult({
  result,
}: {
  result: AnalyzeResponse | null;
}) {

  if (!result) {
    return (
      <Card>
        <EmptyState>
          Run an analysis to see the intelligence report here.
        </EmptyState>
      </Card>
    );
  }

  const topContribution = Math.max(
    ...result.major_contributors.map((c) => c.risk_contribution),
    0.0001
  );

  return (

    <Card className="p-5">

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
        Portfolio Intelligence Report
      </h2>

      <p className="max-w-prose text-sm leading-relaxed text-[var(--ink)]">
        {result.summary ?? "No summary was generated for this run."}
      </p>

      {

        result.risk_change && (

          <div className="mt-5">

            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
              Risk Change
            </h3>

            <div className="grid grid-cols-3 gap-3">

              <StatTile
                label="Volatility"
                value={formatSignedPercent(result.risk_change.volatility_change)}
                tone={deltaTone(result.risk_change.volatility_change)}
              />

              <StatTile
                label="VaR (95%)"
                value={formatSignedPercent(result.risk_change.var_change)}
                tone={deltaTone(result.risk_change.var_change, true)}
              />

              <StatTile
                label="Sharpe"
                value={formatSignedNumber(result.risk_change.sharpe_change, 2)}
                tone={deltaTone(result.risk_change.sharpe_change)}
              />

            </div>

          </div>

        )

      }

      {

        result.major_contributors.length > 0 && (

          <div className="mt-5">

            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
              Major Contributors
            </h3>

            <div className="space-y-2">

              {

                result.major_contributors.map(
                  (contributor, index) => (

                    <div
                      key={index}
                      className="flex items-center gap-3"
                    >

                      <span className="w-14 shrink-0 text-sm font-medium">
                        {contributor.ticker}
                      </span>

                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--gridline)]">
                        <div
                          className="h-full rounded-full bg-[var(--accent)]"
                          style={{
                            width: `${(contributor.risk_contribution / topContribution) * 100}%`,
                          }}
                        />
                      </div>

                      <span className="w-12 shrink-0 text-right text-sm tabular-nums text-[var(--ink-2)]">
                        {(contributor.risk_contribution * 100).toFixed(1)}%
                      </span>

                    </div>

                  )
                )

              }

            </div>

          </div>

        )

      }

      <div className="mt-5">

        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
          Sources
        </h3>

        {

          result.sources.length === 0 ? (

            <p className="text-sm text-[var(--ink-3)]">
              No document sources cited.
            </p>

          ) : (

            <ul className="space-y-1">

              {

                result.sources.map(
                  (source, index) => (

                    <li
                      key={index}
                      className="text-sm text-[var(--ink-2)]"
                    >
                      {source.document}
                      {
                        source.page != null &&
                          ` — Page ${source.page}`
                      }
                    </li>

                  )
                )

              }

            </ul>

          )

        }

      </div>

    </Card>

  );
}
