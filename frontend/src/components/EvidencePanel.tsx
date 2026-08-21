"use client";

import { deltaTone } from "@/lib/format";
import { Card, SectionTitle, EmptyState, Badge } from "@/components/ui";

export type EvidenceItem = {
  source_type: string;
  title?: string;
  company?: string;
  page?: number;
  ticker?: string;
  change_percent?: number;
  published_at?: string;
  url?: string;
  score?: number;
};

export type Evidence = {
  internal: EvidenceItem[];
  market: EvidenceItem[];
  external: EvidenceItem[];
};

const toneText: Record<string, string> = {
  good: "text-[var(--good)]",
  critical: "text-[var(--critical)]",
  neutral: "text-[var(--ink-2)]",
};

export default function EvidencePanel({
  evidence,
}: {
  evidence: Evidence | null;
}) {

  if (!evidence) {
    return null;
  }

  const totalCount =
    evidence.internal.length + evidence.market.length + evidence.external.length;

  return (

    <Card>

      <SectionTitle count={totalCount}>
        Evidence
      </SectionTitle>

      <div className="space-y-5 px-5 py-5">

        <section>

          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
            Internal Documents
          </h3>

          {

            evidence.internal.length === 0 ? (

              <p className="text-sm text-[var(--ink-3)]">
                No internal filings referenced.
              </p>

            ) : (

              <ul className="space-y-2">

                {

                  evidence.internal.map(
                    (item, index) => (

                      <li
                        key={index}
                        className="flex items-center justify-between gap-3 text-sm"
                      >

                        <span className="truncate">
                          {item.title ?? item.company}
                        </span>

                        {
                          item.page != null && (
                            <Badge>
                              p.{item.page}
                            </Badge>
                          )
                        }

                      </li>

                    )
                  )

                }

              </ul>

            )

          }

        </section>

        <section>

          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
            Market Data
          </h3>

          {

            evidence.market.length === 0 ? (

              <p className="text-sm text-[var(--ink-3)]">
                No market movement flagged.
              </p>

            ) : (

              <ul className="space-y-2">

                {

                  evidence.market.map(
                    (item, index) => (

                      <li
                        key={index}
                        className="flex items-center justify-between text-sm"
                      >

                        <span className="font-medium">
                          {item.ticker}
                        </span>

                        {
                          item.change_percent != null && (
                            <span
                              className={`tabular-nums ${toneText[deltaTone(item.change_percent)]}`}
                            >
                              {item.change_percent > 0 ? "+" : ""}
                              {item.change_percent.toFixed(2)}%
                            </span>
                          )
                        }

                      </li>

                    )
                  )

                }

              </ul>

            )

          }

        </section>

        <section>

          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
            External Events
          </h3>

          {

            evidence.external.length === 0 ? (

              <p className="text-sm text-[var(--ink-3)]">
                No external news referenced.
              </p>

            ) : (

              <ul className="space-y-3">

                {

                  evidence.external.map(
                    (item, index) => (

                      <li
                        key={index}
                        className="text-sm"
                      >

                        {
                          item.url ? (

                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-medium text-[var(--accent)] hover:underline"
                            >
                              {item.title}
                            </a>

                          ) : (

                            <span className="font-medium">
                              {item.title}
                            </span>

                          )
                        }

                        {
                          item.published_at && (
                            <p className="text-xs text-[var(--ink-3)]">
                              Published: {item.published_at}
                            </p>
                          )
                        }

                      </li>

                    )
                  )

                }

              </ul>

            )

          }

        </section>

      </div>

    </Card>

  );
}
