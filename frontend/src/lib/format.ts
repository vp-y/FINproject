export function formatAgentName(name?: string): string {

  if (!name) {
    return "System";
  }

  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export type Tone = "good" | "warning" | "critical" | "neutral";

/** Sign -> tone, with `invert` for metrics where a more negative delta is
 * actually worse (e.g. VaR, which is itself a negative number — a bigger
 * drop means MORE downside risk, not less). */
export function deltaTone(value: number, invert = false, epsilon = 1e-4): Tone {

  // Two consecutive risk snapshots rarely land on exactly 0 even when
  // nothing meaningfully changed — floating-point noise from
  // recomputing the same historical window a moment apart shouldn't
  // read as a real risk increase/decrease.
  if (Math.abs(value) < epsilon) {
    return "neutral";
  }

  const isPositive = value > 0;
  const isGood = invert ? !isPositive : isPositive;

  return isGood ? "good" : "critical";
}

export function formatSignedPercent(value: number, digits = 2): string {

  const percent = value * 100;
  const sign = percent > 0 ? "+" : "";

  return `${sign}${percent.toFixed(digits)}%`;
}

export function formatSignedNumber(value: number, digits = 4): string {

  const sign = value > 0 ? "+" : "";

  return `${sign}${value.toFixed(digits)}`;
}
