"use client";

import { Card, SectionTitle, EmptyState, Badge } from "@/components/ui";
import Sparkline from "@/components/Sparkline";
import { formatSignedPercent } from "@/lib/format";
import type { AlternativeCandidate, Horizon } from "@/lib/types";

function CandidateCard({ candidate }: { candidate: AlternativeCandidate }) {

  const isPositive = (candidate.change_percent ?? 0) >= 0;

  return (

    <div className="flex flex-col gap-3 rounded-lg border border-[var(--border)] p-3">

      <div className="flex items-start justify-between gap-2">

        <div className="min-w-0">
          <p className="text-sm font-medium">{candidate.candidate_ticker}</p>
          <p className="truncate text-xs text-[var(--ink-3)]">{candidate.candidate_name}</p>
        </div>

        {
          candidate.replaces_ticker && (
            <Badge tone="neutral">replaces {candidate.replaces_ticker}</Badge>
          )
        }

      </div>

      <Sparkline values={candidate.sparkline ?? []} positive={isPositive} />

      <div className="flex items-center justify-between">

        <span className="text-sm font-semibold tabular-nums">
          {candidate.current_price != null ? `$${candidate.current_price.toFixed(2)}` : "—"}
        </span>

        {
          candidate.change_percent != null && (
            <span
              className={`text-xs font-medium tabular-nums ${
                isPositive ? "text-[var(--good)]" : "text-[var(--critical)]"
              }`}
            >
              {isPositive ? "▲" : "▼"} {formatSignedPercent(candidate.change_percent / 100)}
            </span>
          )
        }

      </div>

      <ul className="space-y-0.5 border-t border-[var(--gridline)] pt-2">
        {
          candidate.rationale.map((reason, index) => (
            <li key={index} className="text-xs text-[var(--ink-2)]">
              {reason}
            </li>
          ))
        }
      </ul>

    </div>

  );
}

export default function AlternativesPanel({
  alternatives,
  diversificationSuggestions,
  horizonFilter,
}: {
  alternatives: AlternativeCandidate[];
  diversificationSuggestions: AlternativeCandidate[];
  horizonFilter: "all" | Horizon;
}) {

  const matches = (candidate: AlternativeCandidate) =>
    horizonFilter === "all" || candidate.horizon === horizonFilter;

  const combined = [
    ...alternatives.filter(matches),
    ...diversificationSuggestions.filter(matches),
  ];

  return (

    <Card>

      <SectionTitle count={combined.length}>
        Alternative Investments
      </SectionTitle>

      {

        combined.length === 0 ? (

          <EmptyState>
            No alternatives suggested for this horizon.
          </EmptyState>

        ) : (

          <div className="grid grid-cols-1 gap-3 px-5 pb-5 pt-2 sm:grid-cols-2 lg:grid-cols-3">
            {
              combined.map((candidate, index) => (
                <CandidateCard key={`${candidate.candidate_ticker}-${index}`} candidate={candidate} />
              ))
            }
          </div>

        )

      }

    </Card>

  );
}
