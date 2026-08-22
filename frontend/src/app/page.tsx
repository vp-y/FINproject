"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, EmptyState } from "@/components/ui";
import type { PortfolioSummary } from "@/lib/types";

export default function Home() {

  const [portfolios, setPortfolios] = useState<PortfolioSummary[] | null>(null);

  useEffect(() => {

    api.get<PortfolioSummary[]>("/portfolio")
      .then((response) => setPortfolios(response.data))
      .catch(() => setPortfolios([]));

  }, []);

  return (

    <div className="min-h-screen">

      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Aegis Intelligence Platform
            </h1>
            <p className="text-sm text-[var(--ink-2)]">
              Pick a portfolio, or bring in a new one.
            </p>
          </div>

          <Link
            href="/onboarding"
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-ink)]"
          >
            + New Portfolio
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">

        {

          portfolios === null ? (

            <p className="text-sm text-[var(--ink-3)]">
              Loading portfolios...
            </p>

          ) : portfolios.length === 0 ? (

            <Card>
              <EmptyState>
                No portfolios yet — click &quot;New Portfolio&quot; to bring in your holdings.
              </EmptyState>
            </Card>

          ) : (

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

              {

                portfolios.map((portfolio) => (

                  <Link
                    key={portfolio.id}
                    href={`/dashboard/${portfolio.id}`}
                  >
                    <Card className="p-5 transition-colors hover:border-[var(--accent)]">

                      <h2 className="text-sm font-semibold">
                        {portfolio.name}
                      </h2>

                      <p className="mt-1 text-sm text-[var(--ink-2)]">
                        {portfolio.holding_count} holding{portfolio.holding_count === 1 ? "" : "s"}
                      </p>

                      <p className="mt-3 text-xs text-[var(--ink-3)]">
                        {
                          portfolio.last_recommendation_at
                            ? `Last analyzed ${new Date(portfolio.last_recommendation_at).toLocaleDateString()}`
                            : "Not yet analyzed"
                        }
                      </p>

                    </Card>
                  </Link>

                ))

              }

            </div>

          )

        }

        <p className="mt-8 text-sm text-[var(--ink-3)]">
          Looking for the free-text risk console instead?{" "}
          <Link href="/analyze" className="text-[var(--accent)] hover:underline">
            Open it here
          </Link>
          .
        </p>

      </main>

    </div>

  );

}
