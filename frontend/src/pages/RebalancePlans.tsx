import { useEffect, useMemo, useState } from "react";
import {
  createRebalancePlan,
  executeBatch,
  fetchRebalancePlan,
  recalcPlan,
} from "../services/portfolio";
import type { RebalancePlan } from "../types";

const STORAGE_KEY = "fs-last-plan-id";

export default function RebalancePlans() {
  const [plan, setPlan] = useState<RebalancePlan | null>(null);

  const loadPlan = async (planId: number) => {
    const data = await fetchRebalancePlan(planId);
    setPlan(data);
  };

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      void loadPlan(Number(stored));
    }
  }, []);

  const createPlan = async () => {
    const data = await createRebalancePlan({
      batch_interval_days: 7,
      recalc_each_batch: true,
    });
    localStorage.setItem(STORAGE_KEY, String(data.plan_id));
    await loadPlan(data.plan_id);
  };

  const execute = async (batchNo: number) => {
    if (!plan) return;
    await executeBatch(plan.id, batchNo);
    await loadPlan(plan.id);
  };

  const recalc = async () => {
    if (!plan) return;
    await recalcPlan(plan.id);
    await loadPlan(plan.id);
  };

  const tradesByBatch = useMemo(() => {
    if (!plan) return {};
    const grouped: Record<string, RebalancePlan["trades"]> = {};
    plan.trades.forEach((trade) => {
      const key = trade.batch_no ? `第${trade.batch_no}批` : "卖出";
      grouped[key] = grouped[key] || [];
      grouped[key].push(trade);
    });
    return grouped;
  }, [plan]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>调仓计划管理</h1>
          <p>生成调仓计划，分批执行并可按批次重算。</p>
        </div>
        <div className="actions">
          <button onClick={() => void createPlan()}>
            <i className="fa-solid fa-plus" /> 生成计划
          </button>
          {plan && (
            <button className="secondary" onClick={() => void recalc()}>
              重新计算剩余批次
            </button>
          )}
        </div>
      </div>

      <div className="card">
        {plan ? (
          <>
            <h3>计划详情</h3>
            <p>
              状态：{plan.status} · 创建时间 {new Date(plan.created_at).toLocaleString()}
            </p>
            <p>总资产：{plan.total_assets.toFixed(2)}</p>

            {Object.entries(tradesByBatch).map(([batch, trades]) => (
              <div key={batch} style={{ marginBottom: 16 }}>
                <strong>{batch}</strong>
                <ul className="list">
                  {trades.map((trade) => (
                    <li key={trade.id}>
                      {trade.action.toUpperCase()} {trade.fund_name} ({trade.fund_code}) -{" "}
                      {trade.amount.toFixed(2)} [{trade.status}]
                    </li>
                  ))}
                </ul>
                {batch !== "卖出" && (
                  <button className="secondary" onClick={() => void execute(Number(batch.replace(/\D/g, "")))}>
                    执行 {batch}
                  </button>
                )}
              </div>
            ))}
          </>
        ) : (
          <p>暂无调仓计划，请先生成。</p>
        )}
      </div>
    </div>
  );
}
