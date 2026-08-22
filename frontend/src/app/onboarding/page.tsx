"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAgentWebSocket } from "@/hooks/useAgentWebSocket";
import { Card, Badge } from "@/components/ui";
import AgentMonitor from "@/components/AgentMonitor";
import DocumentCollectionProgress from "@/components/DocumentCollectionProgress";
import type {
  HoldingResolution,
  CreatePortfolioResponse,
  OnboardingStatus,
  RiskTolerance,
  InvestmentHorizon,
} from "@/lib/types";

type Row = {
  id: string;
  input: string;
  quantity: string;
  purchasePrice: string;
  resolution: HoldingResolution | null;
  resolving: boolean;
};

function emptyRow(): Row {
  return {
    id: crypto.randomUUID(),
    input: "",
    quantity: "",
    purchasePrice: "",
    resolution: null,
    resolving: false,
  };
}

const RESOLUTION_TONE: Record<string, "good" | "warning" | "critical"> = {
  matched: "good",
  ambiguous: "warning",
  not_found: "critical",
};

// Soft guidance only (the user's onboarding run has no hard holding
// cap) — large portfolios just take longer, since each holding is a
// real SEC fetch + rate-limited RAG embed cycle.
const SOFT_ROW_WARNING_THRESHOLD = 15;

const RESOLVE_DEBOUNCE_MS = 400;

type Step = "holdings" | "profile" | "collecting" | "done";

export default function OnboardingPage() {

  const router = useRouter();
  const { events, connected, sessionId } = useAgentWebSocket();

  const [step, setStep] = useState<Step>("holdings");
  const [rows, setRows] = useState<Row[]>([emptyRow()]);
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const [userName, setUserName] = useState("");
  const [portfolioName, setPortfolioName] = useState("");
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance>("moderate");
  const [investmentHorizon, setInvestmentHorizon] = useState<InvestmentHorizon>("medium");
  const [investmentGoal, setInvestmentGoal] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);

  const fetchResolution = (rowId: string, input: string) => {

    api.post("/portfolio/resolve-ticker", { input })
      .then((response) => {
        setRows((previous) =>
          previous.map((row) =>
            row.id === rowId
              ? { ...row, resolution: response.data, resolving: false }
              : row
          )
        );
      })
      .catch(() => {
        setRows((previous) =>
          previous.map((row) =>
            row.id === rowId ? { ...row, resolving: false } : row
          )
        );
      });

  };

  const handleInputChange = (rowId: string, input: string) => {

    setRows((previous) =>
      previous.map((row) =>
        row.id === rowId
          ? { ...row, input, resolution: null, resolving: input.trim().length > 0 }
          : row
      )
    );

    if (timers.current[rowId]) {
      clearTimeout(timers.current[rowId]);
    }

    if (!input.trim()) {
      return;
    }

    timers.current[rowId] = setTimeout(
      () => fetchResolution(rowId, input),
      RESOLVE_DEBOUNCE_MS
    );

  };

  const pickAlternative = (rowId: string, ticker: string) => {

    setRows((previous) =>
      previous.map((row) =>
        row.id === rowId ? { ...row, input: ticker, resolving: true } : row
      )
    );

    fetchResolution(rowId, ticker);

  };

  const updateRowField = (
    rowId: string,
    field: "quantity" | "purchasePrice",
    value: string
  ) => {
    setRows((previous) =>
      previous.map((row) =>
        row.id === rowId ? { ...row, [field]: value } : row
      )
    );
  };

  const addRow = () => setRows((previous) => [...previous, emptyRow()]);

  const removeRow = (rowId: string) =>
    setRows((previous) =>
      previous.length > 1 ? previous.filter((row) => row.id !== rowId) : previous
    );

  const allResolved =
    rows.length > 0 &&
    rows.every(
      (row) =>
        row.resolution?.status === "matched" &&
        Number(row.quantity) > 0 &&
        Number(row.purchasePrice) > 0
    );

  const submitPortfolio = () => {

    setSubmitting(true);
    setSubmitError(null);

    api.post<CreatePortfolioResponse>("/portfolio", {
      user_name: userName.trim() || "Guest",
      portfolio_name: portfolioName.trim() || "My Portfolio",
      holdings: rows.map((row) => ({
        input: row.resolution?.ticker ?? row.input,
        quantity: Number(row.quantity),
        purchase_price: Number(row.purchasePrice),
      })),
      profile: {
        risk_tolerance: riskTolerance,
        investment_horizon: investmentHorizon,
        investment_goal: investmentGoal.trim() || null,
      },
    })
      .then((response) => {

        const id = response.data.portfolio_id;
        setPortfolioId(id);

        return api.post(`/onboarding/${id}/start-collection`, null, {
          params: { session_id: sessionId },
        });
      })
      .then(() => {
        setStep("collecting");
      })
      .catch((err) => {
        console.log(err);
        setSubmitError("Failed to create portfolio — is the backend running?");
      })
      .finally(() => {
        setSubmitting(false);
      });

  };

  // Poll for status while collecting — survives a refresh (the WS
  // connection wouldn't), and carries richer per-ticker detail than the
  // WS feed alone (fetching/indexing states, not just start/end).
  useEffect(() => {

    if (step !== "collecting" || portfolioId == null) {
      return;
    }

    let cancelled = false;

    const poll = () => {
      api.get<OnboardingStatus>(`/onboarding/${portfolioId}/status`)
        .then((response) => {

          if (cancelled) return;

          setOnboardingStatus(response.data);

          if (
            response.data.overall_status === "completed" ||
            response.data.overall_status === "completed_with_errors"
          ) {
            setStep("done");
          }

        })
        .catch(() => {});
    };

    poll();
    const interval = setInterval(poll, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };

  }, [step, portfolioId]);

  const indexedCount =
    onboardingStatus?.holdings.filter((h) => h.status === "indexed").length ?? 0;
  const failedCount =
    onboardingStatus?.holdings.filter(
      (h) => h.status === "failed" || h.status === "no_filing_found"
    ).length ?? 0;

  return (

    <div className="min-h-screen">

      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto max-w-3xl px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight">
            New Portfolio
          </h1>
          <p className="text-sm text-[var(--ink-2)]">
            Tell us what you hold — we&apos;ll find the tickers, pull each
            company&apos;s filings, and get ready for analysis.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-6 px-6 py-8">

        {

          step === "holdings" && (

            <Card className="p-5">

              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
                Your Holdings
              </h2>

              <div className="space-y-3">

                {

                  rows.map((row) => (

                    <div
                      key={row.id}
                      className="rounded-lg border border-[var(--border)] p-3"
                    >

                      <div className="flex gap-2">

                        <input
                          value={row.input}
                          onChange={(event) => handleInputChange(row.id, event.target.value)}
                          placeholder="Ticker or company name (e.g. Apple)"
                          className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                        />

                        <input
                          value={row.quantity}
                          onChange={(event) => updateRowField(row.id, "quantity", event.target.value)}
                          placeholder="Shares"
                          inputMode="decimal"
                          className="w-24 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                        />

                        <input
                          value={row.purchasePrice}
                          onChange={(event) => updateRowField(row.id, "purchasePrice", event.target.value)}
                          placeholder="Avg. cost"
                          inputMode="decimal"
                          className="w-24 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                        />

                        <button
                          onClick={() => removeRow(row.id)}
                          disabled={rows.length === 1}
                          className="rounded-lg px-2 text-sm text-[var(--ink-3)] transition-opacity hover:text-[var(--critical)] disabled:cursor-not-allowed disabled:opacity-30"
                          aria-label="Remove holding"
                        >
                          ✕
                        </button>

                      </div>

                      <div className="mt-2">

                        {
                          row.resolving && (
                            <span className="text-xs text-[var(--ink-3)]">Looking up…</span>
                          )
                        }

                        {
                          !row.resolving && row.resolution && (

                            <div className="flex flex-wrap items-center gap-2">

                              <Badge tone={RESOLUTION_TONE[row.resolution.status]}>
                                {
                                  row.resolution.status === "matched"
                                    ? `${row.resolution.ticker} — ${row.resolution.matched_name}`
                                    : row.resolution.status === "ambiguous"
                                    ? "Did you mean…"
                                    : "Not found"
                                }
                              </Badge>

                              {
                                row.resolution.status !== "matched" &&
                                row.resolution.alternatives.map((alt) => (
                                  <button
                                    key={alt.ticker}
                                    onClick={() => pickAlternative(row.id, alt.ticker)}
                                    className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--ink-2)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
                                  >
                                    {alt.ticker} — {alt.name}
                                  </button>
                                ))
                              }

                            </div>

                          )
                        }

                      </div>

                    </div>

                  ))

                }

              </div>

              <button
                onClick={addRow}
                className="mt-3 text-sm font-medium text-[var(--accent)] hover:opacity-80"
              >
                + Add Holding
              </button>

              {
                rows.length > SOFT_ROW_WARNING_THRESHOLD && (
                  <p className="mt-3 text-xs text-[var(--ink-3)]">
                    {rows.length} holdings queued — collection can take a
                    while (each one is a real filing fetch + document
                    indexing step), but there&apos;s no limit.
                  </p>
                )
              }

              <button
                onClick={() => setStep("profile")}
                disabled={!allResolved}
                className="mt-5 w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-[var(--accent-ink)] transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
              </button>

            </Card>

          )

        }

        {

          step === "profile" && (

            <Card className="p-5">

              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
                About You
              </h2>

              <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
                Your name
              </label>
              <input
                value={userName}
                onChange={(event) => setUserName(event.target.value)}
                placeholder="Guest"
                className="mb-4 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              />

              <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
                Portfolio name
              </label>
              <input
                value={portfolioName}
                onChange={(event) => setPortfolioName(event.target.value)}
                placeholder="My Portfolio"
                className="mb-4 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              />

              <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
                Risk tolerance
              </label>
              <select
                value={riskTolerance}
                onChange={(event) => setRiskTolerance(event.target.value as RiskTolerance)}
                className="mb-4 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>

              <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
                Investment horizon
              </label>
              <select
                value={investmentHorizon}
                onChange={(event) => setInvestmentHorizon(event.target.value as InvestmentHorizon)}
                className="mb-4 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              >
                <option value="short">Short-term</option>
                <option value="medium">Medium-term</option>
                <option value="long">Long-term</option>
              </select>

              <label className="mb-1 block text-xs font-medium text-[var(--ink-2)]">
                What are you investing for? (optional)
              </label>
              <input
                value={investmentGoal}
                onChange={(event) => setInvestmentGoal(event.target.value)}
                placeholder="e.g. retirement, a house down payment..."
                className="mb-5 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              />

              <div className="flex gap-3">

                <button
                  onClick={() => setStep("holdings")}
                  className="rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm font-medium text-[var(--ink-2)] hover:border-[var(--accent)]"
                >
                  Back
                </button>

                <button
                  onClick={submitPortfolio}
                  disabled={submitting || !connected}
                  className="flex-1 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-[var(--accent-ink)] transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {submitting ? "Creating..." : "Create Portfolio"}
                </button>

              </div>

              {
                !connected && !submitting && (
                  <p className="mt-2 text-xs text-[var(--ink-3)]">
                    Waiting for live connection to the backend...
                  </p>
                )
              }

              {
                submitError && (
                  <p className="mt-2 text-xs text-[var(--critical)]">
                    {submitError}
                  </p>
                )
              }

            </Card>

          )

        }

        {

          step === "collecting" && (

            <div className="space-y-6">

              <p className="text-sm text-[var(--ink-2)]">
                Collecting each company&apos;s latest annual report and
                indexing it — this can take a few minutes per holding.
              </p>

              <DocumentCollectionProgress status={onboardingStatus} />

              <AgentMonitor events={events} connected={connected} />

            </div>

          )

        }

        {

          step === "done" && portfolioId != null && (

            <Card className="p-5 text-center">

              <h2 className="mb-2 text-lg font-semibold">
                Portfolio Ready
              </h2>

              <p className="mb-5 text-sm text-[var(--ink-2)]">
                {indexedCount} document{indexedCount === 1 ? "" : "s"} indexed
                {
                  failedCount > 0 &&
                    `, ${failedCount} couldn't be collected (you can still analyze — those holdings just won't have filing-based evidence).`
                }
              </p>

              <button
                onClick={() => router.push(`/dashboard/${portfolioId}`)}
                className="rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-[var(--accent-ink)]"
              >
                Go to Dashboard
              </button>

            </Card>

          )

        }

      </main>

    </div>

  );

}
