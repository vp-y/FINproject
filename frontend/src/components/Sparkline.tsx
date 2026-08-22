"use client";

const WIDTH = 100;
const HEIGHT = 32;
const STROKE = 2; // thin mark, per dataviz mark spec

export default function Sparkline({
  values,
  positive,
}: {
  values: number[];
  /** Line color — good/critical text tokens, never the series color
   * (this is a delta cue, not a categorical identity). */
  positive: boolean;
}) {

  if (!values || values.length < 2) {
    return (
      <div
        className="flex h-8 w-full items-center justify-center text-[10px] text-[var(--ink-3)]"
        style={{ width: WIDTH }}
      >
        No trend data
      </div>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * WIDTH;
    // Inverted: SVG y grows downward, a higher value should sit higher.
    const y = HEIGHT - ((value - min) / range) * HEIGHT;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const color = positive ? "var(--good)" : "var(--critical)";

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="none"
      className="w-full"
      role="img"
      aria-label={positive ? "Upward trend" : "Downward trend"}
    >
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );

}
