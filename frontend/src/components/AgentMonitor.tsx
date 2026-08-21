"use client";

import type { AgentEvent } from "@/hooks/useAgentWebSocket";
import { formatAgentName } from "@/lib/format";
import { Card, EmptyState } from "@/components/ui";

function StatusDot({ type }: { type: string }) {

  if (type === "error") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--critical-soft)] text-[10px] font-bold text-[var(--critical)]">
        ✗
      </span>
    );
  }

  if (
    type === "agent_completed" ||
    type === "tool_completed" ||
    type === "final_result"
  ) {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--good-soft)] text-[10px] font-bold text-[var(--good)]">
        ✓
      </span>
    );
  }

  if (type === "agent_started" || type === "tool_started") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center">
        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent)]" />
      </span>
    );
  }

  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center">
      <span className="h-2.5 w-2.5 rounded-full border-2 border-[var(--ink-3)]" />
    </span>
  );
}

export default function AgentMonitor({
  events,
  connected,
}: {
  events: AgentEvent[];
  connected: boolean;
}) {

  return (

    <Card>

      <div className="flex items-center justify-between px-5 pt-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
          Agent Execution
        </h2>

        <span className="flex items-center gap-1.5 text-xs font-medium text-[var(--ink-3)]">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              connected ? "bg-[var(--good)]" : "bg-[var(--ink-3)]"
            }`}
          />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {

        events.length === 0 ? (

          <EmptyState>
            No activity yet — submit a query to begin.
          </EmptyState>

        ) : (

          <ul className="max-h-96 space-y-3 overflow-y-auto px-5 py-5">

            {

              events.map(
                (event, index) => (

                  <li
                    key={index}
                    className="flex gap-3"
                  >

                    <StatusDot type={event.type} />

                    <div className="min-w-0">

                      <p className="text-sm font-medium">
                        {formatAgentName(event.agent)}
                        {
                          event.tool && (
                            <span className="ml-2 text-xs font-normal text-[var(--ink-3)]">
                              {event.tool}
                            </span>
                          )
                        }
                      </p>

                      <p className="truncate text-sm text-[var(--ink-2)]">
                        {event.message}
                      </p>

                    </div>

                  </li>

                )
              )

            }

          </ul>

        )

      }

    </Card>

  );
}
