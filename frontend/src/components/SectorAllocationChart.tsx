"use client";

import { Card, SectionTitle, EmptyState } from "@/components/ui";

// Fixed order — color follows the sector identity, never its rank in a
// given portfolio, so the same sector always gets the same color across
// renders/portfolios. Matches backend/data/sector_universe.py's key
// order. Only the first 8 get a categorical slot (the validated
// palette's adjacent-pair guarantees stop there); anything past that
// folds into "Other" rather than generating a new hue.
const SECTOR_ORDER = [
  "Technology",
  "Healthcare",
  "Financial Services",
  "Consumer Cyclical",
  "Consumer Defensive",
  "Industrials",
  "Energy",
  "Utilities",
  "Real Estate",
  "Basic Materials",
  "Communication Services",
];

const SERIES_VARS = [
  "--series-1", "--series-2", "--series-3", "--series-4",
  "--series-5", "--series-6", "--series-7", "--series-8",
];

function colorForSector(sector: string): string {
  const index = SECTOR_ORDER.indexOf(sector);
  if (index === -1 || index >= SERIES_VARS.length) {
    return "var(--series-other)";
  }
  return `var(${SERIES_VARS[index]})`;
}

const RADIUS = 60;
const STROKE = 22;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const SEGMENT_GAP = 2; // thin surface gap between wedges, per mark spec

export default function SectorAllocationChart({
  sectorWeights,
}: {
  sectorWeights: Record<string, number>;
}) {

  const entries = Object.entries(sectorWeights).filter(([, weight]) => weight > 0);

  if (entries.length === 0) {
    return (
      <Card>
        <SectionTitle>Sector Allocation</SectionTitle>
        <EmptyState>No sector data available.</EmptyState>
      </Card>
    );
  }

  // Largest first — reads more naturally starting from 12 o'clock.
  const sorted = [...entries].sort((a, b) => b[1] - a[1]);

  let cumulativeOffset = 0;

  const segments = sorted.map(([sector, weight]) => {

    const color = colorForSector(sector);
    const arcLength = Math.max(weight * CIRCUMFERENCE - SEGMENT_GAP, 0);
    const dashArray = `${arcLength} ${CIRCUMFERENCE - arcLength}`;
    const dashOffset = -cumulativeOffset;

    cumulativeOffset += weight * CIRCUMFERENCE;

    return { sector, weight, color, dashArray, dashOffset };

  });

  const topSector = sorted[0];
  const size = 2 * (RADIUS + STROKE / 2);

  return (

    <Card>

      <SectionTitle>
        Sector Allocation
      </SectionTitle>

      <div className="flex flex-col items-center gap-5 px-5 pb-5 pt-2 sm:flex-row">

        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="shrink-0 -rotate-90"
          role="img"
          aria-label="Sector allocation donut chart"
        >
          <g transform={`translate(${size / 2}, ${size / 2})`}>

            <circle r={RADIUS} fill="none" stroke="var(--gridline)" strokeWidth={STROKE} />

            {
              segments.map((segment) => (
                <circle
                  key={segment.sector}
                  r={RADIUS}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={STROKE}
                  strokeDasharray={segment.dashArray}
                  strokeDashoffset={segment.dashOffset}
                  strokeLinecap="butt"
                >
                  <title>{`${segment.sector}: ${(segment.weight * 100).toFixed(1)}%`}</title>
                </circle>
              ))
            }

          </g>

        </svg>

        <div className="min-w-0 flex-1">

          <p className="mb-3 text-center sm:text-left">
            <span className="block text-2xl font-semibold tabular-nums">
              {(topSector[1] * 100).toFixed(0)}%
            </span>
            <span className="text-xs text-[var(--ink-3)]">
              {topSector[0]}
            </span>
          </p>

          <ul className="space-y-1.5">
            {

              segments.map((segment) => (

                <li
                  key={segment.sector}
                  className="flex items-center justify-between gap-3 text-sm"
                >

                  <span className="flex min-w-0 items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: segment.color }}
                    />
                    <span className="truncate text-[var(--ink-2)]">
                      {segment.sector}
                    </span>
                  </span>

                  <span className="shrink-0 tabular-nums text-[var(--ink)]">
                    {(segment.weight * 100).toFixed(0)}%
                  </span>

                </li>

              ))

            }
          </ul>

        </div>

      </div>

    </Card>

  );

}
