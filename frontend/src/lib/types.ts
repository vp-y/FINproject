// Shared types for the portfolio onboarding / recommendation dashboard /
// chat feature set. AnalysisResult.tsx/EvidencePanel.tsx keep their own
// local exported types (AnalyzeResponse, Evidence, EvidenceItem) since
// those predate this file and nothing here needs to redeclare them —
// this file only covers the new surface area.

export type HoldingAlternativeMatch = {
  ticker: string;
  name: string;
  confidence: number;
};

export type HoldingResolution = {
  input: string;
  ticker: string | null;
  matched_name: string | null;
  confidence: number;
  status: "matched" | "ambiguous" | "not_found";
  alternatives: HoldingAlternativeMatch[];
};

export type CreatedHolding = {
  holding_id: number;
  ticker: string;
  matched_name: string | null;
};

export type CreatePortfolioResponse = {
  portfolio_id: number;
  user_id: number;
  created_holdings: CreatedHolding[];
  needs_confirmation: HoldingResolution[];
};

export type RiskTolerance = "conservative" | "moderate" | "aggressive";
export type InvestmentHorizon = "short" | "medium" | "long";

export type PortfolioProfile = {
  risk_tolerance: RiskTolerance;
  investment_horizon: InvestmentHorizon;
  investment_goal: string | null;
};

export type HoldingRow = {
  id: number;
  ticker: string;
  quantity: number;
  purchase_price: number;
};

export type PortfolioDetail = {
  id: number;
  name: string;
  user_id: number;
  profile: PortfolioProfile | null;
  holdings: HoldingRow[];
  document_status_summary: Record<string, number>;
};

export type PortfolioSummary = {
  id: number;
  name: string;
  user_id: number;
  holding_count: number;
  last_recommendation_at: string | null;
};

export type HoldingDocumentStatusValue =
  | "pending"
  | "fetching"
  | "indexing"
  | "indexed"
  | "failed"
  | "no_filing_found";

export type HoldingDocumentStatus = {
  ticker: string;
  status: HoldingDocumentStatusValue;
  document_path: string | null;
  chunk_count: number | null;
  error: string | null;
  updated_at: string | null;
};

export type OnboardingStatus = {
  portfolio_id: number;
  holdings: HoldingDocumentStatus[];
  overall_status: "not_started" | "in_progress" | "completed" | "completed_with_errors";
};

// --- Recommendation dashboard ---------------------------------------

export type WeaknessSeverity = "high" | "medium" | "low";

export type Weakness = {
  id: string;
  category: string;
  severity: WeaknessSeverity;
  description: string;
  metric_evidence: Record<string, unknown>;
};

export type Verdict = "sell" | "reduce" | "hold" | "increase";
export type Horizon = "short_term" | "long_term";
export type Valuation = "overvalued" | "undervalued" | "fair" | "unknown";

export type ExpectedImpact = {
  volatility_delta: number | null;
  sharpe_delta: number | null;
  var_delta: number | null;
  hhi_delta: number | null;
  top_sector_weight_delta: number | null;
};

export type HoldingAction = {
  ticker: string;
  verdict: Verdict;
  weight: number;
  risk_contribution: number;
  risk_contribution_ratio: number;
  risk_adjusted_return: number;
  valuation: Valuation;
  sector: string | null;
  reasoning: string[];
  horizon: Horizon;
  expected_impact: ExpectedImpact;
  current_price?: number | null;
  change_percent?: number | null;
  sparkline?: number[];
};

export type AlternativeCandidate = {
  replaces_ticker: string | null;
  candidate_ticker: string;
  candidate_name: string;
  sector: string;
  risk_adjusted_return?: number;
  valuation?: Valuation;
  rationale: string[];
  horizon: Horizon;
  current_price?: number | null;
  change_percent?: number | null;
  sparkline?: number[];
};

export type MetricsComparisonRow = {
  metric: string;
  label: string;
  current: number;
  recommended: number;
  delta: number;
  invert: boolean;
};

export type BenchmarkComparison = {
  beta: number | null;
  alpha: number | null;
  tracking_error: number | null;
  benchmark_sharpe_ratio: number | null;
  portfolio_annual_return: number | null;
  benchmark_annual_return: number | null;
};

export type PortfolioMetricsBundle = {
  volatility: number;
  sharpe_ratio: number;
  var_95: number;
  weights: Record<string, number>;
  total_value?: number;
  positions: Record<string, unknown>[];
  sector_weights: Record<string, number>;
  top_sector: string | null;
  top_sector_weight: number;
  concentration_flag?: boolean;
  herfindahl_index: number;
  effective_number_of_positions: number;
  average_pairwise_correlation: number;
  correlation_matrix?: Record<string, Record<string, number>>;
  benchmark: BenchmarkComparison;
  max_drawdown: number;
  max_drawdown_trough_date?: string | null;
};

export type RecommendationSource = {
  document?: string | null;
  page?: number | null;
  company?: string | null;
};

export type RecommendationPayload = {
  portfolio_id: number;
  session_id?: string;
  summary: string | null;
  weaknesses: Weakness[];
  holding_actions: HoldingAction[];
  alternatives: AlternativeCandidate[];
  diversification_suggestions: AlternativeCandidate[];
  current_metrics: PortfolioMetricsBundle | null;
  recommended_metrics: PortfolioMetricsBundle | null;
  metrics_comparison: MetricsComparisonRow[];
  sources?: RecommendationSource[];
  status?: string;
  generated_at?: string | null;
};

// --- Chat -------------------------------------------------------------

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  created_at?: string;
};
