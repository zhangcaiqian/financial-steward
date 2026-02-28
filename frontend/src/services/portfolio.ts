import { apiFetch } from "./api";
import type {
  ChatMessage,
  Fund,
  PortfolioSummary,
  RebalancePlan,
  Settings,
} from "../types";

export function fetchSummary() {
  return apiFetch<PortfolioSummary>("/portfolio/summary");
}

export function fetchFunds() {
  return apiFetch<Fund[]>("/funds");
}

export function createFund(payload: {
  code: string;
  name: string;
  fund_type: string;
  cycle_weights: Record<string, number>;
}) {
  return apiFetch("/funds", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFund(
  fundId: number,
  payload: {
    name?: string;
    fund_type?: string;
    cycle_weights?: Record<string, number>;
  }
) {
  return apiFetch(`/funds/${fundId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function upsertHolding(payload: {
  fund_code: string;
  shares: number;
  avg_cost: number;
}) {
  return apiFetch("/holdings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function depositCash(amount: number) {
  return apiFetch("/cash/deposit", {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export function syncNavs() {
  return apiFetch("/prices/sync", { method: "POST" });
}

export function manualNav(payload: {
  fund_code: string;
  nav: number;
  nav_date?: string;
}) {
  return apiFetch("/prices/manual", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createRebalancePlan(payload: {
  batch_interval_days: number;
  recalc_each_batch: boolean;
}) {
  return apiFetch<{ plan_id: number }>("/portfolio/rebalance", {
    method: "POST",
    body: JSON.stringify({ persist: true, ...payload }),
  });
}

export function fetchRebalancePlan(planId: number) {
  return apiFetch<RebalancePlan>(`/portfolio/rebalance/${planId}`);
}

export function executeBatch(planId: number, batchNo: number) {
  return apiFetch(`/portfolio/rebalance/${planId}/execute/${batchNo}`, {
    method: "POST",
  });
}

export function recalcPlan(planId: number) {
  return apiFetch(`/portfolio/rebalance/${planId}/recalculate`, {
    method: "POST",
  });
}

export function chatIngest(text: string) {
  return apiFetch("/chat/ingest", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function chatConfirm(chatId: number) {
  return apiFetch("/chat/confirm", {
    method: "POST",
    body: JSON.stringify({ chat_id: chatId }),
  });
}

export function fetchChatHistory() {
  return apiFetch<ChatMessage[]>("/chat/history");
}

export function fetchSettings() {
  return apiFetch<Settings>("/settings");
}

export function updateSettings(payload: Partial<Settings>) {
  return apiFetch("/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchCycleTargets() {
  return apiFetch<Record<string, number>>("/cycles/targets");
}

export function updateCycleTargets(targets: Record<string, number>) {
  return apiFetch("/cycles/targets", {
    method: "PUT",
    body: JSON.stringify({ targets }),
  });
}

export function fetchPrompt(name: string) {
  return apiFetch<{ name: string; content: string }>(`/prompts/${name}`);
}

export function updatePrompt(name: string, content: string) {
  return apiFetch("/prompts", {
    method: "PUT",
    body: JSON.stringify({ name, content }),
  });
}
