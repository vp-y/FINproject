"use client";

import type { ReactNode } from "react";
import type { Tone } from "@/lib/format";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {

  return (
    <div
      className={`rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function SectionTitle({
  children,
  count,
}: {
  children: ReactNode;
  count?: number;
}) {

  return (
    <div className="flex items-center gap-2 px-5 pt-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--ink-2)]">
        {children}
      </h2>
      {
        count != null && (
          <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-medium text-[var(--accent)]">
            {count}
          </span>
        )
      }
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {

  return (
    <p className="px-5 pb-5 text-sm text-[var(--ink-3)]">
      {children}
    </p>
  );
}

const badgeTones: Record<string, string> = {
  good: "bg-[var(--good-soft)] text-[var(--good)]",
  warning: "bg-[var(--warning-soft)] text-[var(--warning)]",
  critical: "bg-[var(--critical-soft)] text-[var(--critical)]",
  neutral: "bg-[var(--accent-soft)] text-[var(--accent)]",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "good" | "warning" | "critical" | "neutral";
}) {

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badgeTones[tone]}`}
    >
      {children}
    </span>
  );
}

const statTileToneText: Record<Tone, string> = {
  good: "text-[var(--good)]",
  warning: "text-[var(--warning)]",
  critical: "text-[var(--critical)]",
  neutral: "text-[var(--ink)]",
};

const statTileIconBadge: Record<Tone, string> = {
  good: "bg-[var(--good-soft)] text-[var(--good)]",
  warning: "bg-[var(--warning-soft)] text-[var(--warning)]",
  critical: "bg-[var(--critical-soft)] text-[var(--critical)]",
  neutral: "bg-[var(--accent-soft)] text-[var(--accent)]",
};

export function StatTile({
  label,
  value,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: string;
  tone?: Tone;
  /** A single emoji — kept dependency-free, matching the rest of the
   * app's icon-free design (no icon library anywhere else in it). */
  icon?: string;
}) {

  return (
    <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-4 py-3">

      {
        icon && (
          <span
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm ${statTileIconBadge[tone]}`}
            aria-hidden="true"
          >
            {icon}
          </span>
        )
      }

      <div className="min-w-0">
        <p className="truncate text-xs text-[var(--ink-3)]">
          {label}
        </p>
        <p className={`text-lg font-semibold tabular-nums ${statTileToneText[tone]}`}>
          {value}
        </p>
      </div>

    </div>
  );
}
