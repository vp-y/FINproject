"use client";

import type { OnboardingStatus } from "@/lib/types";
import { Card, SectionTitle, Badge, EmptyState } from "@/components/ui";

const STATUS_TONE: Record<string, "good" | "warning" | "critical" | "neutral"> = {
  pending: "neutral",
  fetching: "warning",
  indexing: "warning",
  indexed: "good",
  failed: "critical",
  no_filing_found: "critical",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "Queued",
  fetching: "Fetching filing…",
  indexing: "Indexing…",
  indexed: "Indexed",
  failed: "Failed",
  no_filing_found: "No filing found",
};

export default function DocumentCollectionProgress({
  status,
}: {
  status: OnboardingStatus | null;
}) {

  return (

    <Card>

      <SectionTitle count={status?.holdings.length}>
        Document Collection
      </SectionTitle>

      {

        !status || status.holdings.length === 0 ? (

          <EmptyState>
            Waiting for collection to start…
          </EmptyState>

        ) : (

          <ul className="space-y-2 px-5 pb-5 pt-2">

            {

              status.holdings.map((holding) => (

                <li
                  key={holding.ticker}
                  className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] px-3 py-2"
                >

                  <div className="min-w-0">

                    <p className="text-sm font-medium">
                      {holding.ticker}
                    </p>

                    {
                      holding.error && (
                        <p
                          className="truncate text-xs text-[var(--critical)]"
                          title={holding.error}
                        >
                          {holding.error}
                        </p>
                      )
                    }

                  </div>

                  <Badge tone={STATUS_TONE[holding.status] ?? "neutral"}>
                    {STATUS_LABEL[holding.status] ?? holding.status}
                  </Badge>

                </li>

              ))

            }

          </ul>

        )

      }

    </Card>

  );
}
