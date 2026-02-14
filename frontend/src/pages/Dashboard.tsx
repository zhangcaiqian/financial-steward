import { useEffect, useState } from "react";
import EChart from "../components/charts/EChart";
import { fetchSummary, syncNavs } from "../services/portfolio";
import type { PortfolioSummary } from "../types";

const cycleLabels: Record<string, string> = {
  strong_recovery: "强复苏",
  weak_recovery: "弱复苏",
  weak_recession: "弱衰退",
  strong_recession: "强衰退",
};

const cycleColors: Record<string, string> = {
  strong_recovery: "#f97316",
  weak_recovery: "#facc15",
  weak_recession: "#10b981",
  strong_recession: "#3b82f6",
};

export default function Dashboard() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);

  const load = async () => {
    const data = await fetchSummary();
    setSummary(data);
  };

  useEffect(() => {
    void load();
  }, []);

  const cycleData = summary
    ? Object.entries(summary.cycle_allocations || {}).map(([key, value]) => ({
        name: cycleLabels[key] || key,
        value,
        itemStyle: { color: cycleColors[key] || "#94a3b8" },
      }))
    : [];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>资产配置总览</h1>
          <p>展示当前资产规模、周期配置与调仓偏离情况。</p>
        </div>
        <button onClick={() => void syncNavs().then(load)}>
          <i className="fa-solid fa-rotate" /> 同步净值
        </button>
      </div>

      <div className="grid">
        <div className="card">
          <h3>核心指标</h3>
          {summary ? (
            <div className="metrics">
              <div>
                <span>总资产</span>
                <strong>{summary.total_assets.toFixed(2)}</strong>
              </div>
              <div>
                <span>现金</span>
                <strong>{summary.cash_balance.toFixed(2)}</strong>
              </div>
              <div>
                <span>调仓提示</span>
                <strong>{summary.should_rebalance ? "需要" : "稳定"}</strong>
              </div>
            </div>
          ) : (
            <p>加载中...</p>
          )}
        </div>

        <div className="card">
          <h3>周期配置占比</h3>
          {summary ? (
            <EChart
              option={{
                tooltip: { trigger: "item" },
                series: [
                  {
                    type: "pie",
                    radius: ["40%", "70%"],
                    data: cycleData,
                    label: { formatter: "{b}: {d}%" },
                  },
                ],
              }}
            />
          ) : (
            <p>暂无数据</p>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h3>基金偏离情况</h3>
        {summary?.funds?.length ? (
          <table className="table">
            <thead>
              <tr>
                <th>基金</th>
                <th>市值</th>
                <th>目标占比</th>
                <th>偏离金额</th>
              </tr>
            </thead>
            <tbody>
              {summary.funds.map((fund) => (
                <tr key={fund.code}>
                  <td>
                    {fund.name} ({fund.code})
                  </td>
                  <td>{fund.value.toFixed(2)}</td>
                  <td>{(fund.target_weight * 100).toFixed(2)}%</td>
                  <td>{fund.delta_value.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>暂无基金数据</p>
        )}
      </div>
    </div>
  );
}
