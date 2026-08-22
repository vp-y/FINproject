"use client";

import { Card, SectionTitle, EmptyState, Badge } from "@/components/ui";
import type { Weakness } from "@/lib/types";

const SEVERITY_TONE: Record<string, "critical" | "warning" | "neutral"> = {
  high: "critical",
  medium: "warning",
  low: "neutral",
};

export default function WeaknessesPanel({
  weaknesses,
}: {
  weaknesses: Weakness[];
}) {

  return (

    <Card>

      <SectionTitle count={weaknesses.length}>
        Identified Weaknesses
      </SectionTitle>

      {

        weaknesses.length === 0 ? (

          <EmptyState>
            No significant weaknesses identified.
          </EmptyState>

        ) : (

          <ul className="space-y-3 px-5 pb-5 pt-2">

            {

              weaknesses.map((weakness) => (

                <li
                  key={weakness.id}
                  className="rounded-lg border border-[var(--border)] p-3"
                >

                  <div className="mb-1 flex items-center gap-2">
                    <Badge tone={SEVERITY_TONE[weakness.severity] ?? "neutral"}>
                      {weakness.severity}
                    </Badge>
                    <span className="text-xs uppercase tracking-wide text-[var(--ink-3)]">
                      {weakness.category}
                    </span>
                  </div>

                  <p className="text-sm text-[var(--ink)]">
                    {weakness.description}
                  </p>

                </li>

              ))

            }

          </ul>

        )

      }

    </Card>

  );
}
