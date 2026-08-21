"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { AnalyzeResponse } from "@/components/AnalysisResult";
import { Card } from "@/components/ui";

export default function AnalysisForm({
  sessionId,
  connected,
  onResult,
}: {
  sessionId: string | null;
  connected: boolean;
  onResult: (result: AnalyzeResponse) => void;
}) {

  const [portfolioId, setPortfolioId] = useState("1");

  const [query, setQuery] = useState(
    "Why did my portfolio risk increase?"
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = () => {

    setLoading(true);
    setError(null);

    api.post("/agents/analyze", {
      portfolio_id: Number(portfolioId),
      query,
      session_id: sessionId,
    })
      .then((response) => {
        onResult(response.data);
      })
      .catch((err) => {
        console.log(err);
        setError("Request failed — is the backend running?");
      })
      .finally(() => {
        setLoading(false);
      });

  };

  return (

    <Card className="p-5">

      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
        New Analysis
      </h2>

      <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
        Portfolio ID
      </label>

      <input

        value={portfolioId}

        onChange={(event) =>
          setPortfolioId(
            event.target.value
          )
        }

        className="mb-4 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"

      />

      <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
        Query
      </label>

      <textarea

        value={query}

        onChange={(event) =>
          setQuery(
            event.target.value
          )
        }

        rows={4}

        className="mb-4 w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"

      />

      <button

        onClick={analyze}

        disabled={loading || !connected}

        className="w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-[var(--accent-ink)] transition-opacity disabled:cursor-not-allowed disabled:opacity-40"

      >

        {loading ? "Analyzing..." : "Analyze Portfolio"}

      </button>

      {
        !connected && !loading && (
          <p className="mt-2 text-xs text-[var(--ink-3)]">
            Waiting for live connection to the backend...
          </p>
        )
      }

      {
        error && (
          <p className="mt-2 text-xs text-[var(--critical)]">
            {error}
          </p>
        )
      }

    </Card>

  );

}
