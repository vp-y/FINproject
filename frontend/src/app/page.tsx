"use client";

import { useState } from "react";
import { useAgentWebSocket } from "@/hooks/useAgentWebSocket";
import AgentMonitor from "@/components/AgentMonitor";
import AnalysisForm from "@/components/AnalysisForm";
import AnalysisResult, { type AnalyzeResponse } from "@/components/AnalysisResult";
import EvidencePanel from "@/components/EvidencePanel";

export default function Home() {

  const { events, connected, sessionId } = useAgentWebSocket();

  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  return (

    <div className="min-h-screen">

      <header className="border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Aegis Intelligence Platform
            </h1>
            <p className="text-sm text-[var(--ink-2)]">
              Agentic portfolio risk analysis
            </p>
          </div>

          <span className="flex items-center gap-2 text-xs font-medium text-[var(--ink-2)]">
            <span
              className={`h-2 w-2 rounded-full ${
                connected ? "bg-[var(--good)]" : "bg-[var(--ink-3)]"
              }`}
            />
            {connected ? "Live" : "Offline"}
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">

        <div className="space-y-6">
          <AnalysisForm
            sessionId={sessionId}
            connected={connected}
            onResult={setResult}
          />

          <AgentMonitor
            events={events}
            connected={connected}
          />
        </div>

        <div className="space-y-6">
          <AnalysisResult
            result={result}
          />

          <EvidencePanel
            evidence={result?.evidence ?? null}
          />
        </div>

      </main>

    </div>

  );

}
