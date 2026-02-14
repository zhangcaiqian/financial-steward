export type FundCycle = {
  cycle: string;
  weight: number;
};

export type Fund = {
  id: number;
  code: string;
  name: string;
  fund_type: string;
  currency?: string;
  cycles?: FundCycle[];
  primary_cycle?: string | null;
};

export type FundSnapshot = {
  fund_id: number;
  code: string;
  name: string;
  fund_type: string;
  shares: number;
  nav: number;
  value: number;
  target_weight: number;
  target_value: number;
  delta_value: number;
  cycle_weights: Record<string, number>;
};

export type PortfolioSummary = {
  should_rebalance: boolean;
  total_assets: number;
  cash_balance: number;
  cash_target: number;
  cycle_allocations: Record<string, number>;
  funds: FundSnapshot[];
};

export type RebalanceBatch = {
  id: number;
  batch_no: number;
  due_at: string;
  status: string;
};

export type RebalanceTrade = {
  id: number;
  action: string;
  amount: number;
  status: string;
  batch_no: number | null;
  fund_code: string;
  fund_name: string;
};

export type RebalancePlan = {
  id: number;
  status: string;
  total_assets: number;
  cash_balance: number;
  cash_target: number;
  should_rebalance: boolean;
  recalc_each_batch: boolean;
  created_at: string;
  batches: RebalanceBatch[];
  trades: RebalanceTrade[];
};

export type Settings = {
  rebalance_frequency_days: number;
  rebalance_threshold_ratio: number;
  cash_target_ratio: number;
  dca_batches: number;
};

export type ChatMessage = {
  id: number;
  text: string;
  status: string;
  parsed: any;
  provider?: string;
  model?: string;
  created_at: string;
  applied_at?: string | null;
};
